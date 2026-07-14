# tests/api/test_auth.py
def test_login_success(client, citizen_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "citizen1", "password": "pass1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "citizen1"
    assert data["user"]["role_code"] == "citizen"


def test_login_wrong_password(client, citizen_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "citizen1", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_user(client, citizen_user, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "citizen1"


def test_menus_returns_role_menus(client, citizen_user, auth_headers):
    response = client.get("/api/v1/permissions/menus", headers=auth_headers)
    assert response.status_code == 200
    assert "citizen_report" in response.json()["menus"]


def test_login_unknown_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "whatever"},
    )
    assert response.status_code == 401


def test_login_disabled_account(client, db, seeded_roles):
    from app.core.security import hash_password
    from app.models.user import User

    u = User(
        username="disabled1",
        password_hash=hash_password("pass1234"),
        email="disabled@example.com",
        role_id=seeded_roles["citizen"].id,
        status="disabled",
    )
    db.add(u)
    db.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "disabled1", "password": "pass1234"},
    )
    assert response.status_code == 403


def test_register_creates_user_with_emailed_code(client, db, seeded_roles):
    provider = _configure_auth_email(client, db)
    send = client.post(
        "/api/v1/auth/register/email-code",
        json={"email": " New@Example.COM "},
    )
    assert send.status_code == 202

    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "password": "pass1234",
        "phone": "138",
        "email": " New@Example.COM ",
        "verification_code": _extract_code(provider),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["username"] == "newuser"
    assert data["user"]["role_code"] == "citizen"

    from app.models.user import User
    assert db.query(User).filter_by(username="newuser").one().email == "new@example.com"


def test_register_duplicate_username_409(client, citizen_user):
    resp = client.post("/api/v1/auth/register",
                       json={
                           "username": "citizen1",
                           "password": "x",
                           "email": "other@example.com",
                           "verification_code": "000000",
                       })
    assert resp.status_code == 409


def test_register_email_code_existing_email_409(client, db, citizen_user):
    _configure_auth_email(client, db)

    response = client.post(
        "/api/v1/auth/register/email-code",
        json={"email": " CITIZEN@example.com "},
    )

    assert response.status_code == 409


def test_register_email_code_cooldown_429(client, db, seeded_roles):
    _configure_auth_email(client, db)
    payload = {"email": "new@example.com"}

    assert client.post("/api/v1/auth/register/email-code", json=payload).status_code == 202
    assert client.post("/api/v1/auth/register/email-code", json=payload).status_code == 429


def test_register_email_code_delivery_failure_503(client, db, seeded_roles):
    _configure_auth_email(client, db, FailingProvider())

    response = client.post(
        "/api/v1/auth/register/email-code",
        json={"email": "new@example.com"},
    )

    assert response.status_code == 503


def test_register_invalid_code_400(client, db, seeded_roles):
    _configure_auth_email(client, db)

    response = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "password": "pass1234",
        "email": "new@example.com",
        "verification_code": "000000",
    })

    assert response.status_code == 400


def test_update_profile(client, citizen_user, auth_headers):
    resp = client.put("/api/v1/auth/profile", headers=auth_headers,
                      json={"phone": "1390000", "email": "updated@e.com"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "citizen1"


def test_change_password(client, citizen_user, auth_headers):
    resp = client.put("/api/v1/auth/password", headers=auth_headers,
                      json={"old_password": "pass1234", "new_password": "newpass5678"})
    assert resp.status_code == 200
    # 用新密码能登录
    r2 = client.post("/api/v1/auth/login", json={"username": "citizen1", "password": "newpass5678"})
    assert r2.status_code == 200
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401


def test_change_password_wrong_old(client, citizen_user, auth_headers):
    resp = client.put("/api/v1/auth/password", headers=auth_headers,
                      json={"old_password": "wrong", "new_password": "x"})
    assert resp.status_code == 400


def test_password_reset_code_unknown_email_returns_uniform_202(client, db, seeded_roles):
    provider = _configure_auth_email(client, db)

    response = client.post(
        "/api/v1/auth/password-reset/email-code",
        json={"email": "unknown@example.com"},
    )

    assert response.status_code == 202
    assert provider.sent == []


def test_password_reset_code_delivery_failure_returns_uniform_202(
    client, db, citizen_user,
):
    _configure_auth_email(client, db, FailingProvider())

    response = client.post(
        "/api/v1/auth/password-reset/email-code",
        json={"email": citizen_user.email},
    )

    assert response.status_code == 202


def test_password_reset_code_disabled_account_returns_uniform_202(
    client, db, seeded_roles,
):
    from app.core.security import hash_password
    from app.models.user import User

    disabled = User(
        username="disabled-reset",
        password_hash=hash_password("pass1234"),
        email="disabled-reset@example.com",
        role_id=seeded_roles["citizen"].id,
        status="disabled",
    )
    db.add(disabled)
    db.commit()
    provider = _configure_auth_email(client, db)

    response = client.post(
        "/api/v1/auth/password-reset/email-code",
        json={"email": disabled.email},
    )

    assert response.status_code == 202
    assert response.json() == {
        "message": "如果邮箱可用，验证码将发送至该邮箱"
    }
    assert provider.sent == []


def test_password_reset_code_cooldown_returns_uniform_202(
    client, db, citizen_user,
):
    provider = _configure_auth_email(client, db)
    payload = {"email": citizen_user.email}

    first = client.post("/api/v1/auth/password-reset/email-code", json=payload)
    second = client.post("/api/v1/auth/password-reset/email-code", json=payload)

    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    assert len(provider.sent) == 1


def test_password_reset_changes_password_and_invalidates_old_token(
    client, db, citizen_user, auth_headers,
):
    provider = _configure_auth_email(client, db)
    send = client.post(
        "/api/v1/auth/password-reset/email-code",
        json={"email": " CITIZEN@example.com "},
    )
    assert send.status_code == 202

    reset = client.post("/api/v1/auth/password-reset", json={
        "email": citizen_user.email,
        "verification_code": _extract_code(provider),
        "new_password": "newpass5678",
    })

    assert reset.status_code == 200
    assert client.post("/api/v1/auth/login", json={
        "username": "citizen1", "password": "pass1234",
    }).status_code == 401
    assert client.post("/api/v1/auth/login", json={
        "username": "citizen1", "password": "newpass5678",
    }).status_code == 200
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401


def test_password_reset_invalid_code_400(client, db, citizen_user):
    _configure_auth_email(client, db)

    response = client.post("/api/v1/auth/password-reset", json={
        "email": citizen_user.email,
        "verification_code": "000000",
        "new_password": "newpass5678",
    })

    assert response.status_code == 400
import re

from app.core.deps import get_notification_provider
from app.models.violation import NotificationTemplate
from app.services.notification_provider import (
    FakeNotificationProvider,
    NotificationProvider,
    SendResult,
)


def _configure_auth_email(client, db, provider=None):
    db.add_all([
        NotificationTemplate(
            code="register_email_code",
            channel="email",
            subject_template="注册验证码",
            body_template="验证码 {code}",
        ),
        NotificationTemplate(
            code="password_reset_email_code",
            channel="email",
            subject_template="重置验证码",
            body_template="验证码 {code}",
        ),
    ])
    db.commit()
    provider = provider or FakeNotificationProvider()
    client.app.dependency_overrides[get_notification_provider] = lambda: provider
    return provider


def _extract_code(provider):
    return re.search(r"\b(\d{6})\b", provider.sent[-1][2]).group(1)


class FailingProvider(NotificationProvider):
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        return SendResult("failed", error="smtp_send_failed")
