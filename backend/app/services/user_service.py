# app/services/user_service.py
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import Role, User
from app.services.email_verification_service import normalize_email

VALID_USER_STATUS = {"active", "disabled"}


def _get_role_by_code(db: Session, code: str) -> Role:
    role = db.query(Role).filter_by(code=code).first()
    if role is None:
        raise HTTPException(status_code=400, detail=f"角色 {code} 不存在")
    return role


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, *, username: str, password: str, phone: str | None,
                    email: str, role_code: str) -> User:
        if self.db.query(User).filter_by(username=username).first():
            raise HTTPException(status_code=409, detail="用户名已存在")
        normalized_email = normalize_email(email)
        if self.db.query(User).filter_by(email=normalized_email).first():
            raise HTTPException(status_code=409, detail="邮箱已存在")
        role = _get_role_by_code(self.db, role_code)
        user = User(
            username=username,
            password_hash=hash_password(password),
            phone=phone,
            email=normalized_email,
            role_id=role.id,
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
        self.db.refresh(user)
        return user

    def list_users(self, *, page: int, page_size: int,
                   role: str | None = None, status: str | None = None) -> dict:
        q = self.db.query(User)
        if status:
            q = q.filter(User.status == status)
        if role:
            q = q.join(Role, User.role_id == Role.id).filter(Role.code == role)
        total = q.count()
        items = (
            q.order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user

    def update_user(self, user_id: int, *, phone: str | None, email: str | None,
                    role_code: str | None, status: str | None, password: str | None) -> User:
        user = self.get_user(user_id)
        if status is not None and status not in VALID_USER_STATUS:
            raise HTTPException(status_code=400, detail="status 必须是 active 或 disabled")
        if role_code is not None:
            user.role_id = _get_role_by_code(self.db, role_code).id
        if phone is not None:
            user.phone = phone
        if email is not None:
            normalized_email = normalize_email(email)
            duplicate = (
                self.db.query(User)
                .filter(User.email == normalized_email, User.id != user.id)
                .first()
            )
            if duplicate:
                raise HTTPException(status_code=409, detail="邮箱已存在")
            user.email = normalized_email
        if status is not None:
            user.status = status
        if password is not None:
            user.password_hash = hash_password(password)
            user.auth_version += 1
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=409, detail="邮箱已存在")
        self.db.refresh(user)
        return user
