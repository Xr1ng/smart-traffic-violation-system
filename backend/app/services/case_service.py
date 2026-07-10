# app/services/case_service.py
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.intake import Case, IntakeEvent
from app.models.user import User


class CaseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_cases(self, *, user: User, status: str | None = None, source_type: str | None = None,
                   location_text: str | None = None, plate_no: str | None = None,
                   keyword: str | None = None,
                   start_time: datetime | None = None, end_time: datetime | None = None,
                   page: int = 1, page_size: int = 20) -> dict:
        role = user.role.code
        if role == "camera":
            raise HTTPException(status_code=403, detail="摄像头无权查询业务数据")
        q = self.db.query(Case)
        # source_type / source_id / captured_at / location_text 在 IntakeEvent 上，按需关联
        need_join = bool(
            role == "citizen" or location_text or source_type or keyword or start_time or end_time
        )
        if need_join:
            q = q.join(IntakeEvent, Case.intake_event_id == IntakeEvent.id)
        if role == "citizen":
            q = q.filter(IntakeEvent.source_type == "citizen", IntakeEvent.source_id == user.id)
        if status:
            q = q.filter(Case.status == status)
        if source_type:
            q = q.filter(IntakeEvent.source_type == source_type)
        if location_text:
            q = q.filter(IntakeEvent.location_text.ilike(f"%{location_text}%"))
        if start_time:
            q = q.filter(IntakeEvent.captured_at >= start_time)
        if end_time:
            q = q.filter(IntakeEvent.captured_at <= end_time)
        if plate_no:
            q = q.filter(Case.plate_no == plate_no)
        if keyword:
            pattern = f"%{keyword}%"
            q = q.filter(or_(
                Case.case_no.ilike(pattern),
                Case.plate_no.ilike(pattern),
                IntakeEvent.location_text.ilike(pattern),
            ))
        # reviewer / admin: pending_human_review 优先，再 id desc
        if role in ("reviewer", "admin"):
            q = q.order_by(case((Case.status == "pending_human_review", 0), else_=1), Case.id.desc())
        else:
            q = q.order_by(Case.id.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_case_detail(self, case_id: int, *, user: User) -> dict:
        case = self.db.get(Case, case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="案件不存在")
        ev = case.intake_event
        if user.role.code == "citizen" and not (
            ev is not None and ev.source_type == "citizen" and ev.source_id == user.id
        ):
            raise HTTPException(status_code=403, detail="无权查看该案件")
        media_list = [{"asset_type": m.asset_type, "url": m.url} for m in (ev.media_assets if ev else [])]
        # 前端期望 { original_url, annotated_url, cropped_plate_url } 扁平对象
        media = {}
        for m in media_list:
            key = f"{m['asset_type']}_url"
            media[key] = m["url"]
            media.setdefault("original_url", m["url"] if m["asset_type"] == "original" else None)
        # 前端扁平字段（从 intake_event 提取到顶层）
        location_text = ev.location_text if ev else None
        captured_at = str(ev.captured_at) if ev and ev.captured_at else None
        speed = ev.speed if ev else None
        source_desc_map = {"citizen": "市民举报", "camera": "摄像头抓拍", "admin": "后台上传"}
        return {
            "id": case.id, "case_no": case.case_no, "status": case.status,
            "source_type": ev.source_type if ev else None,
            "source_desc": source_desc_map.get(ev.source_type, "") if ev else "",
            "location_text": location_text,
            "captured_at": captured_at,
            "speed": speed,
            "plate_no": case.plate_no, "violation_type": case.violation_type,
            "media": media,
            "detection_result": None,
            "rule_result": None,
            "ai_review": None,
            "review": {"reviewer_id": case.reviewer_id, "review_opinion": case.review_opinion,
                       "reviewed_at": str(case.reviewed_at) if case.reviewed_at else None},
        }
