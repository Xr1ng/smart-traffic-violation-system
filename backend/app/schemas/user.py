from datetime import datetime

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    id: int
    username: str
    phone: str | None
    email: str
    role_code: str
    role_id: int
    status: str
    created_at: datetime


class UserCreateIn(BaseModel):
    username: str
    password: str
    phone: str | None = None
    email: str
    role_code: str


class UserUpdateIn(BaseModel):
    phone: str | None = None
    email: str | None = None
    role_code: str | None = None
    status: str | None = None
    password: str | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int


def to_admin_user_out(user) -> AdminUserOut:
    """User ORM → AdminUserOut（role_code 取自 user.role.code，from_attributes 取不到嵌套）。"""
    return AdminUserOut(
        id=user.id,
        username=user.username,
        phone=user.phone,
        email=user.email,
        role_code=user.role.code,
        role_id=user.role_id,
        status=user.status,
        created_at=user.created_at,
    )
