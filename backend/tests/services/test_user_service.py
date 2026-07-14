import pytest

from app.services.user_service import UserService


def test_create_user(db, seeded_roles):
    u = UserService(db).create_user(
        username="u1", password="pass1234", phone="138", email="u@e.com", role_code="reviewer")
    assert u.id is not None
    assert u.role.code == "reviewer"
    assert u.status == "active"
    assert u.password_hash != "pass1234"


def test_create_user_duplicate_409(db, seeded_roles):
    UserService(db).create_user(username="u1", password="p", phone=None, email="u1@example.com", role_code="citizen")
    with pytest.raises(Exception) as exc:
        UserService(db).create_user(username="u1", password="p", phone=None, email="other@example.com", role_code="citizen")
    assert exc.value.status_code == 409


def test_create_user_role_not_found_400(db, seeded_roles):
    with pytest.raises(Exception) as exc:
        UserService(db).create_user(username="u1", password="p", phone=None, email="u1@example.com", role_code="bogus")
    assert exc.value.status_code == 400


def test_list_users_filter_by_status(db, seeded_roles):
    UserService(db).create_user(username="a", password="p", phone=None, email="a@example.com", role_code="citizen")
    u = UserService(db).create_user(username="b", password="p", phone=None, email="b@example.com", role_code="citizen")
    UserService(db).update_user(u.id, phone=None, email=None, role_code=None, status="disabled", password=None)
    res = UserService(db).list_users(page=1, page_size=20, status="disabled")
    assert res["total"] == 1
    assert res["items"][0].username == "b"


def test_get_user_404(db):
    with pytest.raises(Exception) as exc:
        UserService(db).get_user(9999)
    assert exc.value.status_code == 404


def test_update_user_password_and_role(db, seeded_roles):
    u = UserService(db).create_user(username="u1", password="p", phone=None, email="u1@example.com", role_code="citizen")
    old_hash = u.password_hash
    updated = UserService(db).update_user(
        u.id, phone=None, email=None, role_code="reviewer", status=None, password="newpass")
    assert updated.password_hash != old_hash
    assert updated.role.code == "reviewer"
    assert updated.auth_version == 1


def test_update_user_invalid_status_400(db, seeded_roles):
    u = UserService(db).create_user(username="u1", password="p", phone=None, email="u1@example.com", role_code="citizen")
    with pytest.raises(Exception) as exc:
        UserService(db).update_user(u.id, phone=None, email=None, role_code=None, status="bogus", password=None)
    assert exc.value.status_code == 400


def test_create_user_normalizes_email_and_rejects_duplicate(db, seeded_roles):
    first = UserService(db).create_user(
        username="u1", password="p", phone=None,
        email=" User@Example.COM ", role_code="citizen",
    )
    assert first.email == "user@example.com"

    with pytest.raises(Exception) as exc:
        UserService(db).create_user(
            username="u2", password="p", phone=None,
            email="USER@example.com", role_code="citizen",
        )
    assert exc.value.status_code == 409
