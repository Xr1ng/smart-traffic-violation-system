# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_notification_provider
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.auth import (
    EmailCodeRequest,
    LoginRequest,
    MenusOut,
    PasswordChangeRequest,
    PasswordResetRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.email_verification_service import (
    EmailCodeCooldown,
    EmailDeliveryFailed,
    EmailVerificationService,
    InvalidEmailCode,
    normalize_email,
)
from app.services.notification_provider import NotificationProvider
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="用户已禁用")
    token = create_access_token(
        subject=str(user.id),
        role=user.role.code,
        auth_version=user.auth_version,
    )
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, username=user.username, role_code=user.role.code),
    )


ROLE_MENUS: dict[str, list[str]] = {
    "citizen": ["citizen_report", "my_violations"],
    "reviewer": ["review_workbench", "violations_query"],
    "admin": ["review_workbench", "violations_query", "system_management", "statistics"],
    "camera": [],
}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, username=user.username, role_code=user.role.code)


permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permissions_router.get("/menus", response_model=MenusOut)
def menus(user: User = Depends(get_current_user)) -> MenusOut:
    return MenusOut(menus=ROLE_MENUS.get(user.role.code, []))


def _verification_service(
    db: Session,
    provider: NotificationProvider,
) -> EmailVerificationService:
    return EmailVerificationService(db, NotificationService(db, provider))


@router.post("/register/email-code", status_code=status.HTTP_202_ACCEPTED)
def send_register_email_code(
    body: EmailCodeRequest,
    db: Session = Depends(get_db),
    provider: NotificationProvider = Depends(get_notification_provider),
) -> dict:
    email = normalize_email(body.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="邮箱已存在")
    try:
        _verification_service(db, provider).send_code(email, "register")
    except EmailCodeCooldown:
        raise HTTPException(status_code=429, detail="验证码发送过于频繁")
    except EmailDeliveryFailed:
        raise HTTPException(status_code=503, detail="邮件发送失败，请稍后重试")
    return {"message": "验证码已发送"}


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    provider: NotificationProvider = Depends(get_notification_provider),
) -> TokenResponse:
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    email = normalize_email(body.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="邮箱已存在")
    try:
        _verification_service(db, provider).consume_code(
            email, "register", body.verification_code
        )
    except InvalidEmailCode:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    role = db.query(Role).filter(Role.code == "citizen").first()
    if role is None:
        raise HTTPException(status_code=500, detail="系统未初始化角色")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        phone=body.phone,
        email=email,
        role_id=role.id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    db.refresh(user)
    token = create_access_token(
        subject=str(user.id),
        role=user.role.code,
        auth_version=user.auth_version,
    )
    return TokenResponse(
        access_token=token,
        user=UserOut(id=user.id, username=user.username, role_code=user.role.code),
    )


PASSWORD_RESET_RESPONSE = {"message": "如果邮箱可用，验证码将发送至该邮箱"}


@router.post("/password-reset/email-code", status_code=status.HTTP_202_ACCEPTED)
def send_password_reset_email_code(
    body: EmailCodeRequest,
    db: Session = Depends(get_db),
    provider: NotificationProvider = Depends(get_notification_provider),
) -> dict:
    email = normalize_email(body.email)
    user = db.query(User).filter(User.email == email, User.status == "active").first()
    if user is None:
        return PASSWORD_RESET_RESPONSE
    try:
        _verification_service(db, provider).send_code(email, "password_reset")
    except (EmailCodeCooldown, EmailDeliveryFailed):
        pass
    return PASSWORD_RESET_RESPONSE


@router.post("/password-reset")
def reset_password(
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
    provider: NotificationProvider = Depends(get_notification_provider),
) -> dict:
    email = normalize_email(body.email)
    user = (
        db.query(User)
        .filter(User.email == email, User.status == "active")
        .with_for_update()
        .first()
    )
    if user is None:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    try:
        _verification_service(db, provider).consume_code(
            email, "password_reset", body.verification_code
        )
    except InvalidEmailCode:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    user.password_hash = hash_password(body.new_password)
    user.auth_version += 1
    db.commit()
    return {"message": "密码重置成功"}


@router.put("/profile", response_model=UserOut)
def update_profile(body: ProfileUpdateRequest, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> UserOut:
    if body.phone is not None:
        user.phone = body.phone
    if body.email is not None:
        normalized_email = normalize_email(body.email)
        duplicate = (
            db.query(User)
            .filter(User.email == normalized_email, User.id != user.id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="邮箱已存在")
        user.email = normalized_email
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="邮箱已存在")
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, role_code=user.role.code)


@router.put("/password")
def change_password(body: PasswordChangeRequest, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(body.new_password)
    user.auth_version += 1
    db.commit()
    return {"message": "密码修改成功"}
