# app/core/deps.py
import hashlib

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.intake import CameraApiKey, CameraDevice
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="无效的令牌")
    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    if payload.get("auth_version", 0) != user.auth_version:
        raise HTTPException(status_code=401, detail="登录状态已失效")
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.code not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return checker


def get_camera_device(
    x_camera_key: str = Header(..., alias="X-Camera-Key"),
    db: Session = Depends(get_db),
) -> CameraDevice:
    # API key 是高熵随机串，用 sha256 做 key_hash 即可（无需 bcrypt 慢哈希），
    # 按 hash 索引查找 O(1)，避免全表 bcrypt 逐个比对。
    key_hash = hashlib.sha256(x_camera_key.encode()).hexdigest()
    key = (
        db.query(CameraApiKey)
        .filter(CameraApiKey.key_hash == key_hash, CameraApiKey.status == "active")
        .first()
    )
    if key is None:
        raise HTTPException(status_code=401, detail="无效的摄像头密钥")
    dev = db.get(CameraDevice, key.camera_device_id)
    if dev is None or dev.status != "enabled":
        raise HTTPException(status_code=401, detail="摄像头设备不可用")
    return dev


from app.services.notification_provider import EmailSmtpProvider, NotificationProvider


def get_notification_provider() -> NotificationProvider:
    return EmailSmtpProvider()
