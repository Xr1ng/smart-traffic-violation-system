# app/services/notification_service.py
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.violation import Notification, NotificationTemplate, Violation
from app.services.notification_provider import NotificationProvider


class NotificationService:
    def __init__(self, db: Session, provider: NotificationProvider) -> None:
        self.db = db
        self.provider = provider

    def send_template(
        self,
        template_code: str,
        recipient: str | None,
        context: dict[str, object],
        *,
        owner_id: int | None = None,
        violation_id: int | None = None,
        audit_content: str | None = None,
    ) -> Notification:
        tpl = (
            self.db.query(NotificationTemplate)
            .filter(
                NotificationTemplate.code == template_code,
                NotificationTemplate.channel == "email",
                NotificationTemplate.status == "enabled",
            )
            .first()
        )
        if tpl is None:
            return self._record(
                template_code=template_code,
                recipient=recipient,
                subject="",
                body="",
                audit_content=audit_content,
                owner_id=owner_id,
                violation_id=violation_id,
                status="failed",
                error="template_missing",
            )

        try:
            subject = tpl.subject_template.format(**context)
            body = tpl.body_template.format(**context)
        except (KeyError, ValueError, IndexError):
            return self._record(
                template_code=template_code,
                recipient=recipient,
                subject="",
                body="",
                audit_content=audit_content,
                owner_id=owner_id,
                violation_id=violation_id,
                status="failed",
                error="template_render_failed",
            )

        if not recipient:
            return self._record(
                template_code=template_code,
                recipient=None,
                subject=subject,
                body=body,
                audit_content=audit_content,
                owner_id=owner_id,
                violation_id=violation_id,
                status="failed",
                error="no_recipient",
            )

        result = self.provider.send(recipient, subject, body)
        return self._record(
            template_code=template_code,
            recipient=recipient,
            subject=subject,
            body=body,
            audit_content=audit_content,
            owner_id=owner_id,
            violation_id=violation_id,
            status=result.status,
            provider="email",
            provider_msg_id=result.provider_msg_id,
            error=result.error,
        )

    def send_violation_notification(self, violation: Violation, owner_email: str | None) -> Notification:
        ctx = {
            "violation_type": violation.violation_type,
            "plate_no": violation.plate_no,
            "occurred_at": str(violation.occurred_at or ""),
            "location_text": violation.location_text or "",
            "fine_amount": violation.fine_amount,
            "points": violation.points,
            "violation_no": violation.violation_no,
        }
        return self.send_template(
            "violation_notice",
            owner_email,
            ctx,
            owner_id=violation.owner_id,
            violation_id=violation.id,
        )

    def _record(
        self,
        *,
        template_code: str,
        recipient: str | None,
        subject: str,
        body: str,
        status: str,
        owner_id: int | None = None,
        violation_id: int | None = None,
        audit_content: str | None = None,
        provider: str | None = None,
        provider_msg_id: str | None = None,
        error: str | None = None,
    ) -> Notification:
        content = audit_content if audit_content is not None else f"{subject}\n\n{body}"
        if error:
            content += f"\n[error:{error}]"
        n = Notification(
            violation_id=violation_id,
            owner_id=owner_id,
            channel="email",
            recipient=recipient, content=content, status=status, provider=provider,
            provider_msg_id=provider_msg_id,
            template_code=template_code,
            sent_at=datetime.now(timezone.utc) if status == "sent" else None,
        )
        self.db.add(n)
        self.db.flush()
        self.db.refresh(n)
        return n
