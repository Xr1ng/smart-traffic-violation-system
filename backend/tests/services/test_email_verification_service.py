import re
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import verify_password
from app.models.email_verification import EmailVerificationCode
from app.models.violation import NotificationTemplate
from app.services.email_verification_service import (
    EmailCodeCooldown,
    EmailDeliveryFailed,
    EmailVerificationService,
    InvalidEmailCode,
)
from app.services.notification_provider import (
    FakeNotificationProvider,
    NotificationProvider,
    SendResult,
)
from app.services.notification_service import NotificationService


def _seed_templates(db):
    db.add_all([
        NotificationTemplate(
            code="register_email_code",
            channel="email",
            subject_template="注册验证码",
            body_template="验证码 {code}",
        ),
        NotificationTemplate(
            code="password_reset_email_code",
            channel="email",
            subject_template="重置验证码",
            body_template="验证码 {code}",
        ),
    ])
    db.commit()


def _make_service(db, provider=None):
    provider = provider or FakeNotificationProvider()
    return EmailVerificationService(db, NotificationService(db, provider)), provider


def _sent_code(provider):
    return re.search(r"\b(\d{6})\b", provider.sent[-1][2]).group(1)


def test_send_code_stores_hash_normalized_email_and_expiry(db, monkeypatch):
    _seed_templates(db)
    fixed_now = datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "app.services.email_verification_service._utcnow", lambda: fixed_now
    )
    monkeypatch.setattr(
        "app.services.email_verification_service.secrets.randbelow", lambda _: 23456
    )
    service, provider = _make_service(db)

    service.send_code(" User@Example.COM ", "register")

    saved = db.query(EmailVerificationCode).one()
    assert saved.email == "user@example.com"
    assert saved.code_hash != "023456"
    assert verify_password("023456", saved.code_hash)
    expires_at = saved.expires_at.replace(tzinfo=timezone.utc)
    assert expires_at == fixed_now + timedelta(minutes=10)
    assert _sent_code(provider) == "023456"


def test_send_code_enforces_resend_cooldown(db):
    _seed_templates(db)
    service, _ = _make_service(db)
    service.send_code("user@example.com", "register")

    with pytest.raises(EmailCodeCooldown):
        service.send_code("user@example.com", "register")


def test_new_successful_code_invalidates_old_code(db, monkeypatch):
    _seed_templates(db)
    now = [datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc)]
    monkeypatch.setattr(
        "app.services.email_verification_service._utcnow", lambda: now[0]
    )
    generated = iter([111111, 222222])
    monkeypatch.setattr(
        "app.services.email_verification_service.secrets.randbelow",
        lambda _: next(generated),
    )
    service, provider = _make_service(db)
    service.send_code("user@example.com", "register")
    old_code = _sent_code(provider)

    now[0] += timedelta(seconds=61)
    service.send_code("user@example.com", "register")
    new_code = _sent_code(provider)

    with pytest.raises(InvalidEmailCode):
        service.consume_code("user@example.com", "register", old_code)
    service.consume_code("user@example.com", "register", new_code)


class FailingProvider(NotificationProvider):
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        return SendResult("failed", error="smtp_send_failed")


def test_failed_replacement_delivery_preserves_old_code(db, monkeypatch):
    _seed_templates(db)
    now = [datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc)]
    monkeypatch.setattr(
        "app.services.email_verification_service._utcnow", lambda: now[0]
    )
    service, provider = _make_service(db)
    service.send_code("user@example.com", "register")
    old_code = _sent_code(provider)

    now[0] += timedelta(seconds=61)
    failing_service, _ = _make_service(db, FailingProvider())
    with pytest.raises(EmailDeliveryFailed):
        failing_service.send_code("user@example.com", "register")

    service.consume_code("user@example.com", "register", old_code)


def test_consume_code_is_one_time_and_purpose_isolated(db):
    _seed_templates(db)
    service, provider = _make_service(db)
    service.send_code("user@example.com", "register")
    code = _sent_code(provider)

    with pytest.raises(InvalidEmailCode):
        service.consume_code("user@example.com", "password_reset", code)

    service.consume_code("user@example.com", "register", code)
    with pytest.raises(InvalidEmailCode):
        service.consume_code("user@example.com", "register", code)


def test_consume_code_expires_after_ten_minutes(db, monkeypatch):
    _seed_templates(db)
    now = [datetime(2026, 7, 14, 4, 0, tzinfo=timezone.utc)]
    monkeypatch.setattr(
        "app.services.email_verification_service._utcnow", lambda: now[0]
    )
    service, provider = _make_service(db)
    service.send_code("user@example.com", "password_reset")
    code = _sent_code(provider)

    now[0] += timedelta(minutes=10, seconds=1)
    with pytest.raises(InvalidEmailCode):
        service.consume_code("user@example.com", "password_reset", code)


def test_consume_code_stops_after_five_failed_attempts(db):
    _seed_templates(db)
    service, provider = _make_service(db)
    service.send_code("user@example.com", "register")
    correct_code = _sent_code(provider)
    wrong_code = "000000" if correct_code != "000000" else "111111"

    for _ in range(5):
        with pytest.raises(InvalidEmailCode):
            service.consume_code("user@example.com", "register", wrong_code)

    with pytest.raises(InvalidEmailCode):
        service.consume_code("user@example.com", "register", correct_code)
    saved = db.query(EmailVerificationCode).one()
    assert saved.attempt_count == 5


def test_send_code_rejects_unknown_purpose(db):
    _seed_templates(db)
    service, _ = _make_service(db)

    with pytest.raises(ValueError, match="purpose"):
        service.send_code("user@example.com", "unknown")


def test_send_code_renders_configured_expiry_minutes(db, monkeypatch):
    db.add(NotificationTemplate(
        code="register_email_code",
        channel="email",
        subject_template="注册验证码",
        body_template="验证码 {code}，有效 {expires_minutes} 分钟",
    ))
    db.commit()
    monkeypatch.setattr(
        "app.services.email_verification_service.settings.EMAIL_CODE_TTL_SECONDS",
        120,
    )
    service, provider = _make_service(db)

    service.send_code("user@example.com", "register")

    assert "有效 2 分钟" in provider.sent[-1][2]
