# tests/services/test_notification_provider.py
from email import message_from_bytes
from email.header import decode_header, make_header

from app.services.notification_provider import (
    EmailSmtpProvider, FakeNotificationProvider, SendResult,
)


class RecordingSmtp:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_called = False
        self.login_args = None
        self.sent_message = None
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message):
        self.sent_message = message.as_bytes()


def _configure_smtp(monkeypatch, *, security="starttls", user="smtp-user"):
    from app.services import notification_provider as mod

    monkeypatch.setattr(mod.settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(mod.settings, "SMTP_PORT", 587)
    monkeypatch.setattr(mod.settings, "SMTP_FROM", "noreply@example.com")
    monkeypatch.setattr(mod.settings, "SMTP_USER", user)
    monkeypatch.setattr(mod.settings, "SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setattr(mod.settings, "SMTP_SECURITY", security)
    monkeypatch.setattr(mod.settings, "SMTP_TIMEOUT_SECONDS", 7.5)
    RecordingSmtp.instances.clear()
    return mod


def test_fake_provider_records_send():
    p = FakeNotificationProvider()
    r = p.send("o@e.com", "主题", "正文")
    assert isinstance(r, SendResult)
    assert r.status == "sent"
    assert p.sent == [("o@e.com", "主题", "正文")]


def test_email_smtp_provider_missing_config_returns_failed(monkeypatch):
    from app.services import notification_provider as mod
    monkeypatch.setattr(mod.settings, "SMTP_HOST", None)
    p = EmailSmtpProvider()
    r = p.send("o@e.com", "s", "b")
    assert r.status == "failed"
    assert r.error  # 有错误信息


def test_email_smtp_provider_sends_utf8_mime_with_starttls(monkeypatch):
    mod = _configure_smtp(monkeypatch)
    monkeypatch.setattr(mod.smtplib, "SMTP", RecordingSmtp)

    result = EmailSmtpProvider().send("owner@example.com", "中文主题", "中文正文")

    smtp = RecordingSmtp.instances[0]
    message = message_from_bytes(smtp.sent_message)
    assert result.status == "sent"
    assert str(make_header(decode_header(message["Subject"]))) == "中文主题"
    assert message.get_payload(decode=True).decode(message.get_content_charset()) == "中文正文\n"
    assert smtp.starttls_called is True
    assert smtp.login_args == ("smtp-user", "smtp-pass")
    assert smtp.timeout == 7.5


def test_email_smtp_provider_uses_ssl_without_starttls(monkeypatch):
    mod = _configure_smtp(monkeypatch, security="ssl")
    monkeypatch.setattr(mod.smtplib, "SMTP_SSL", RecordingSmtp)

    result = EmailSmtpProvider().send("owner@example.com", "subject", "body")

    assert result.status == "sent"
    assert RecordingSmtp.instances[0].starttls_called is False


def test_email_smtp_provider_none_security_skips_tls_and_login(monkeypatch):
    mod = _configure_smtp(monkeypatch, security="none", user=None)
    monkeypatch.setattr(mod.smtplib, "SMTP", RecordingSmtp)

    result = EmailSmtpProvider().send("owner@example.com", "subject", "body")

    smtp = RecordingSmtp.instances[0]
    assert result.status == "sent"
    assert smtp.starttls_called is False
    assert smtp.login_args is None


def test_email_smtp_provider_rejects_unknown_security_mode(monkeypatch):
    _configure_smtp(monkeypatch, security="invalid")

    result = EmailSmtpProvider().send("owner@example.com", "subject", "body")

    assert result.status == "failed"
    assert result.error == "smtp_invalid_security"


def test_email_smtp_provider_sanitizes_connection_error(monkeypatch):
    mod = _configure_smtp(monkeypatch)

    def fail_connect(*_args, **_kwargs):
        raise OSError("smtp-pass must not leak")

    monkeypatch.setattr(mod.smtplib, "SMTP", fail_connect)

    result = EmailSmtpProvider().send("owner@example.com", "subject", "body")

    assert result.status == "failed"
    assert result.error == "smtp_connection_failed"
    assert "smtp-pass" not in result.error


def test_email_smtp_provider_rejects_invalid_header_without_raising(monkeypatch):
    _configure_smtp(monkeypatch)

    result = EmailSmtpProvider().send(
        "owner@example.com", "invalid\nsubject", "body"
    )

    assert result.status == "failed"
    assert result.error == "smtp_send_failed"
