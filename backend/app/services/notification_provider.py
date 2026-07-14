# app/services/notification_provider.py
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.core.config import settings


@dataclass
class SendResult:
    status: str  # "sent" | "failed"
    provider_msg_id: str | None = None
    error: str | None = None


class NotificationProvider:
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        raise NotImplementedError


class EmailSmtpProvider(NotificationProvider):
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        if not settings.SMTP_HOST or not settings.SMTP_FROM:
            return SendResult("failed", error="smtp_not_configured")
        security = settings.SMTP_SECURITY.lower()
        if security not in {"starttls", "ssl", "none"}:
            return SendResult("failed", error="smtp_invalid_security")

        try:
            message = EmailMessage()
            message["From"] = settings.SMTP_FROM
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)

            smtp_class = smtplib.SMTP_SSL if security == "ssl" else smtplib.SMTP
            with smtp_class(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            ) as s:
                if security == "starttls":
                    s.starttls()
                if settings.SMTP_USER:
                    s.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
                s.send_message(message)
            return SendResult("sent", provider_msg_id="email")
        except smtplib.SMTPAuthenticationError:
            return SendResult("failed", error="smtp_auth_failed")
        except (OSError, smtplib.SMTPConnectError):
            return SendResult("failed", error="smtp_connection_failed")
        except smtplib.SMTPException:
            return SendResult("failed", error="smtp_send_failed")
        except Exception:
            return SendResult("failed", error="smtp_send_failed")


class FakeNotificationProvider(NotificationProvider):
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        self.sent.append((to_email, subject, body))
        return SendResult("sent", provider_msg_id="fake")
