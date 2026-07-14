# app/schemas/auth.py
import re

from pydantic import BaseModel, field_validator


def _validated_email(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise ValueError("邮箱格式无效")
    return normalized


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role_code: str
    phone: str | None = None
    email: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterRequest(BaseModel):
    username: str
    password: str
    phone: str | None = None
    email: str
    verification_code: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validated_email(value)


class ProfileUpdateRequest(BaseModel):
    phone: str | None = None
    email: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return _validated_email(value) if value is not None else None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class MenusOut(BaseModel):
    menus: list[str]


class EmailCodeRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validated_email(value)


class PasswordResetRequest(BaseModel):
    email: str
    verification_code: str
    new_password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validated_email(value)
