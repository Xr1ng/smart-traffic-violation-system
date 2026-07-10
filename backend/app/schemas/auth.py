# app/schemas/auth.py
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    role_code: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterRequest(BaseModel):
    username: str
    password: str
    phone: str | None = None
    email: str | None = None


class ProfileUpdateRequest(BaseModel):
    phone: str | None = None
    email: str | None = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class MenusOut(BaseModel):
    menus: list[str]
