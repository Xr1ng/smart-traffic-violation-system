import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.email_verification import EmailVerificationCode
from app.models.violation import Notification
from app.services.notification_service import NotificationService


VALID_PURPOSES = {"register", "password_reset"}


class EmailCodeCooldown(Exception):
    pass


class EmailDeliveryFailed(Exception):
    pass


class InvalidEmailCode(Exception):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if not normalized:
        raise ValueError("email must not be empty")
    return normalized


class EmailVerificationService:
    def __init__(self, db: Session, notification_service: NotificationService) -> None:
        self.db = db
        self.notification_service = notification_service

    def send_code(self, email: str, purpose: str) -> Notification:
        if purpose not in VALID_PURPOSES:
            raise ValueError("unsupported purpose")
        normalized = normalize_email(email)
        now = _utcnow()
        latest = (
            self.db.query(EmailVerificationCode)
            .filter(
                EmailVerificationCode.email == normalized,
                EmailVerificationCode.purpose == purpose,
            )
            .order_by(EmailVerificationCode.created_at.desc())
            .first()
        )
        if latest is not None:
            elapsed = now - _as_utc(latest.created_at)
            if elapsed < timedelta(seconds=settings.EMAIL_CODE_RESEND_SECONDS):
                raise EmailCodeCooldown()

        plain_code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = hash_password(plain_code)
        template_code = (
            "register_email_code"
            if purpose == "register"
            else "password_reset_email_code"
        )
        audit_content = (
            "注册邮箱验证码邮件"
            if purpose == "register"
            else "密码重置验证码邮件"
        )
        notification = self.notification_service.send_template(
            template_code,
            normalized,
            {
                "code": plain_code,
                "expires_minutes": (settings.EMAIL_CODE_TTL_SECONDS + 59) // 60,
            },
            audit_content=audit_content,
        )
        if notification.status != "sent":
            self.db.commit()
            raise EmailDeliveryFailed()

        (
            self.db.query(EmailVerificationCode)
            .filter(
                EmailVerificationCode.email == normalized,
                EmailVerificationCode.purpose == purpose,
                EmailVerificationCode.used_at.is_(None),
            )
            .update({EmailVerificationCode.used_at: now}, synchronize_session="fetch")
        )
        self.db.add(EmailVerificationCode(
            email=normalized,
            purpose=purpose,
            code_hash=code_hash,
            expires_at=now + timedelta(seconds=settings.EMAIL_CODE_TTL_SECONDS),
            created_at=now,
        ))
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def consume_code(
        self,
        email: str,
        purpose: str,
        code: str,
    ) -> EmailVerificationCode:
        if purpose not in VALID_PURPOSES:
            raise ValueError("unsupported purpose")
        normalized = normalize_email(email)
        now = _utcnow()
        record = (
            self.db.query(EmailVerificationCode)
            .filter(
                EmailVerificationCode.email == normalized,
                EmailVerificationCode.purpose == purpose,
                EmailVerificationCode.used_at.is_(None),
            )
            .order_by(EmailVerificationCode.created_at.desc())
            .with_for_update()
            .first()
        )
        if (
            record is None
            or record.attempt_count >= settings.EMAIL_CODE_MAX_ATTEMPTS
            or _as_utc(record.expires_at) <= now
        ):
            raise InvalidEmailCode()

        if not verify_password(code, record.code_hash):
            record.attempt_count += 1
            self.db.commit()
            raise InvalidEmailCode()

        record.used_at = now
        self.db.flush()
        return record
