# app/services/review_service.py
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.intake import Case
from app.models.user import User
from app.models.violation import AuditLog
from app.services.notification_provider import NotificationProvider
from app.services.notification_service import NotificationService
from app.services.reward_service import RewardService
from app.services.violation_service import ViolationService, get_owner_email


class ReviewService:
    def __init__(self, db: Session, provider: NotificationProvider) -> None:
        self.db = db
        self.violation_service = ViolationService(db)
        self.reward_service = RewardService(db)
        self.notification_service = NotificationService(db, provider)

    def approve(self, case_id: int, user: User, *, plate_no: str, violation_type: str,
                fine_amount: int, points: int, review_opinion: str) -> dict:
        case = self.db.get(Case, case_id)
        if case is None or case.status != "pending_human_review":
            raise HTTPException(status_code=409, detail="案件不在待审核状态")
        if not plate_no:
            raise HTTPException(status_code=400, detail="需提供车牌号")
        now = datetime.now(timezone.utc)
        case.plate_no = plate_no
        case.violation_type = violation_type
        case.reviewer_id = user.id
        case.review_opinion = review_opinion
        case.reviewed_at = now

        violation = self.violation_service.create_violation(
            case, plate_no=plate_no, violation_type=violation_type,
            fine_amount=fine_amount, points=points)
        owner_email = get_owner_email(self.db, violation)

        # source_type / source_id 实际在 IntakeEvent 上（Case 无此字段），
        # 通过 case.intake_event 关联读取，避免 AttributeError。
        ev = case.intake_event
        reward_id = None
        if ev is not None and ev.source_type == "citizen" and ev.source_id:
            reward = self.reward_service.grant_reward(
                citizen_id=ev.source_id, case_id=case.id,
                violation_id=violation.id, violation_type=violation_type)
            reward_id = reward.id

        notification = self.notification_service.send_violation_notification(violation, owner_email)

        self._audit(user, "approve", "case", case.id, f"通过，违章{violation.violation_no}")
        case.status = "notified"
        self.db.commit()
        return {"violation_no": violation.violation_no,
                "notification_status": notification.status, "reward_id": reward_id}

    def reject(self, case_id: int, user: User, *, reject_reason: str) -> dict:
        case = self.db.get(Case, case_id)
        if case is None or case.status != "pending_human_review":
            raise HTTPException(status_code=409, detail="案件不在待审核状态")
        case.status = "rejected"
        case.reviewer_id = user.id
        case.review_opinion = reject_reason
        case.reviewed_at = datetime.now(timezone.utc)
        self._audit(user, "reject", "case", case.id, f"驳回：{reject_reason}")
        self.db.commit()
        return {"case_no": case.case_no, "status": "rejected"}

    def request_recheck(self, case_id: int, user: User) -> dict:
        case = self.db.get(Case, case_id)
        if case is None or case.status != "pending_human_review":
            raise HTTPException(status_code=409, detail="案件不在待审核状态")
        self._audit(user, "request_recheck", "case", case.id, "请求重新 AI 初审")
        self.db.commit()
        return {"message": "AI 复核已排队（Plan 2 接入后生效）"}

    def _audit(self, user: User, action: str, target_type: str, target_id: int, detail: str) -> None:
        self.db.add(AuditLog(actor_id=user.id, action=action, target_type=target_type,
                             target_id=target_id, detail=detail))
