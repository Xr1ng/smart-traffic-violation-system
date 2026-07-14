# tests/core/test_security.py
from app.core.security import hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


from fastapi import HTTPException

from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_token():
    token = create_access_token(subject="42", role="citizen", auth_version=3)
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "citizen"
    assert payload["auth_version"] == 3


def test_decode_invalid_token_raises():
    import pytest

    with pytest.raises(HTTPException) as exc:
        decode_access_token("not-a-token")
    assert exc.value.status_code == 401
