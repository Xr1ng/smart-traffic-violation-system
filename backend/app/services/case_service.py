# app/services/case_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.intake import Case, IntakeEvent
from app.models.user import User


class CaseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_cases(self, *, user: User, status: str | None = None, source_type: str | None = None,
                   location_text: str | None = None, plate_no: str | None = None,
                   page: int = 1, page_size: int = 20) -> dict:
        role = user.role.code
        if role == "camera":
            raise HTTPException(status_code=403, detail="摄像头无权查询业务数据")
        q = self.db.query(Case)
        # source_type / source_id 实际在 IntakeEvent 上（Case 无此字段），按需关联一次。
        if role == "citizen" or location_text or source_type:
            q = q.join(IntakeEvent, Case.intake_event_id == IntakeEvent.id)
        if role == "citizen":
            q = q.filter(IntakeEvent.source_type == "citizen", IntakeEvent.source_id == user.id)
        if status:
            q = q.filter(Case.status == status)
        if source_type:
            q = q.filter(IntakeEvent.source_type == source_type)
        if location_text:
            q = q.filter(IntakeEvent.location_text.ilike(f"%{location_text}%"))
        if plate_no:
            q = q.filter(Case.plate_no == plate_no)
        total = q.count()
        items = q.order_by(Case.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_case_detail(self, case_id: int, *, user: User) -> dict:
        case = self.db.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="案件不存在")
        ev = case.intake_event
        # 市民仅能查看自己举报的案件（source_type/source_id 在 IntakeEvent 上）
        if user.role.code == "citizen" and not (
            ev is not None and ev.source_type == "citizen" and ev.source_id == user.id
        ):
            raise HTTPException(status_code=403, detail="无权查看该案件")
        media = [{"asset_type": m.asset_type, "url": m.url} for m in (ev.media_assets if ev else [])]
        return {
            "id": case.id, "case_no": case.case_no, "status": case.status,
            "source_type": ev.source_type if ev else None,
            "plate_no": case.plate_no, "violation_type": case.violation_type,
            "intake_event": {"location_text": ev.location_text if ev else None,
                             "captured_at": str(ev.captured_at) if ev and ev.captured_at else None,
                             "speed": ev.speed if ev else None},
            "media": media,
            "ai_detection_result": None,
            "violation_rule_result": None,
            "ai_review_result": None,
            "review": {"reviewer_id": case.reviewer_id, "review_opinion": case.review_opinion,
                       "reviewed_at": str(case.reviewed_at) if case.reviewed_at else None},
        }
