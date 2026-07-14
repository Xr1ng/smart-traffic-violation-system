# tests/core/test_deps.py
from fastapi import HTTPException
import pytest

from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token


def test_get_current_user_returns_user(db, citizen_user, citizen_token):
    user = get_current_user(token=citizen_token, db=db)
    assert user.id == citizen_user.id


def test_get_current_user_invalid_token_raises(db):
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="bad", db=db)
    assert exc.value.status_code == 401


def test_require_role_allows(db, citizen_user, citizen_token):
    checker = require_role("citizen", "admin")
    user = checker(user=citizen_user)
    assert user.id == citizen_user.id


def test_require_role_denies(db, citizen_user):
    checker = require_role("admin")
    with pytest.raises(HTTPException) as exc:
        checker(user=citizen_user)
    assert exc.value.status_code == 403


def test_get_current_user_rejects_stale_auth_version(db, citizen_user):
    token = create_access_token(
        subject=str(citizen_user.id),
        role="citizen",
        auth_version=citizen_user.auth_version,
    )
    citizen_user.auth_version += 1
    db.commit()

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db)

    assert exc.value.status_code == 401
