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


def test_register_creates_user_and_returns_token(client, seeded_roles):
    resp = client.post("/api/v1/auth/register",
                       json={"username": "newuser", "password": "pass1234", "phone": "138", "email": "n@e.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["username"] == "newuser"
    assert data["user"]["role_code"] == "citizen"


def test_register_duplicate_username_409(client, citizen_user):
    resp = client.post("/api/v1/auth/register",
                       json={"username": "citizen1", "password": "x"})
    assert resp.status_code == 409


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


def test_change_password_wrong_old(client, citizen_user, auth_headers):
    resp = client.put("/api/v1/auth/password", headers=auth_headers,
                      json={"old_password": "wrong", "new_password": "x"})
    assert resp.status_code == 400
