# tests/services/test_notification_service.py
from app.models.violation import Notification, NotificationTemplate, Violation
from app.services.notification_provider import (
    FakeNotificationProvider,
    NotificationProvider,
    SendResult,
)
from app.services.notification_service import NotificationService


def _seed_template(db):
    db.add(NotificationTemplate(code="violation_notice", subject_template="违章通知:{violation_type}",
                                body_template="车牌{plate_no}于{occurred_at}在{location_text}{violation_type}，罚款{fine_amount}元扣{points}分。"))
    db.commit()


def test_send_with_owner_email_records_sent(db):
    _seed_template(db)
    v = Violation(violation_no="VIO1", case_id=1, plate_no="粤A12345", violation_type="超速",
                  fine_amount=200, points=6, location_text="路口A")
    db.add(v); db.commit()
    svc = NotificationService(db, FakeNotificationProvider())
    n = svc.send_violation_notification(v, "owner@e.com")
    assert n.status == "sent"
    assert n.recipient == "owner@e.com"
    assert "粤A12345" in n.content


def test_send_without_owner_email_records_failed(db):
    _seed_template(db)
    v = Violation(violation_no="VIO2", case_id=1, plate_no="粤B99999", violation_type="超速",
                  fine_amount=200, points=6)
    db.add(v); db.commit()
    svc = NotificationService(db, FakeNotificationProvider())
    n = svc.send_violation_notification(v, None)
    assert n.status == "failed"
    assert n.recipient is None


def test_send_template_logs_redacted_auth_content(db):
    db.add(NotificationTemplate(
        code="register_email_code",
        channel="email",
        subject_template="验证码",
        body_template="验证码 {code}",
    ))
    db.commit()
    provider = FakeNotificationProvider()

    result = NotificationService(db, provider).send_template(
        "register_email_code",
        "user@example.com",
        {"code": "123456"},
        audit_content="注册邮箱验证码邮件",
    )

    assert result.status == "sent"
    assert result.template_code == "register_email_code"
    assert result.content == "注册邮箱验证码邮件"
    assert "123456" not in result.content
    assert provider.sent == [("user@example.com", "验证码", "验证码 123456")]


def test_send_template_missing_template_records_failure(db):
    provider = FakeNotificationProvider()

    result = NotificationService(db, provider).send_template(
        "missing", "user@example.com", {}, audit_content="邮件"
    )

    assert result.status == "failed"
    assert "template_missing" in result.content
    assert provider.sent == []


def test_send_template_render_error_does_not_send(db):
    db.add(NotificationTemplate(
        code="register_email_code",
        channel="email",
        subject_template="验证码",
        body_template="验证码 {code}",
    ))
    db.commit()
    provider = FakeNotificationProvider()

    result = NotificationService(db, provider).send_template(
        "register_email_code", "user@example.com", {}, audit_content="邮件"
    )

    assert result.status == "failed"
    assert "template_render_failed" in result.content
    assert provider.sent == []


class FailingProvider(NotificationProvider):
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        return SendResult("failed", error="smtp_send_failed")


def test_send_template_records_provider_failure(db):
    db.add(NotificationTemplate(
        code="password_reset_email_code",
        channel="email",
        subject_template="重置密码",
        body_template="验证码 {code}",
    ))
    db.commit()

    result = NotificationService(db, FailingProvider()).send_template(
        "password_reset_email_code",
        "user@example.com",
        {"code": "123456"},
        audit_content="密码重置验证码邮件",
    )

    assert result.status == "failed"
    assert "smtp_send_failed" in result.content
    assert "123456" not in result.content
