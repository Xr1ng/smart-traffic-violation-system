# app/services/notification_service.py
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.violation import Notification, NotificationTemplate, Violation
from app.services.notification_provider import NotificationProvider


class NotificationService:
    def __init__(self, db: Session, provider: NotificationProvider) -> None:
        self.db = db
        self.provider = provider

    def send_violation_notification(self, violation: Violation, owner_email: str | None) -> Notification:
        tpl = (
            self.db.query(NotificationTemplate)
            .filter(NotificationTemplate.code == "violation_notice", NotificationTemplate.status == "enabled")
            .first()
        )
        ctx = {
            "violation_type": violation.violation_type,
            "plate_no": violation.plate_no,
            "occurred_at": str(violation.occurred_at or ""),
            "location_text": violation.location_text or "",
            "fine_amount": violation.fine_amount,
            "points": violation.points,
            "violation_no": violation.violation_no,
        }
        subject = tpl.subject_template.format(**ctx) if tpl else "违章通知"
        body = tpl.body_template.format(**ctx) if tpl else ""

        if not owner_email:
            return self._record(violation, None, subject, body, status="failed", error="no_recipient")

        result = self.provider.send(owner_email, subject, body)
        return self._record(
            violation, owner_email, subject, body,
            status=result.status, provider="email",
            provider_msg_id=result.provider_msg_id, error=result.error,
        )

    def _record(self, violation, recipient, subject, body, *, status, provider=None,
                provider_msg_id=None, error=None) -> Notification:
        content = f"{subject}\n\n{body}" + (f"\n[error:{error}]" if error else "")
        n = Notification(
            violation_id=violation.id, owner_id=violation.owner_id, channel="email",
            recipient=recipient, content=content, status=status, provider=provider,
            provider_msg_id=provider_msg_id,
            sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        )
        self.db.add(n)
        self.db.flush()
        self.db.refresh(n)
        return n
