# app/services/case_service.py
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import case, or_
from sqlalchemy.orm import Session

from app.models.intake import Case, IntakeEvent
from app.models.user import User


AI_DISPLAY_TEXT = {
    "illegal_stop detection": "违停检测",
    "vehicle detection": "车辆检测",
    "plate OCR": "车牌识别",
    "plate OCR text": "车牌文字识别",
    "license plate region": "车牌定位",
    "plate recognition": "车牌识别",
    "plate localization": "车牌定位",
    "plate text recognition": "车牌文字识别",
    "illegal_stop": "违停",
    "complete": "完整",
    "partial": "部分",
    "insufficient": "不足",
    "suggest_approve": "建议通过",
    "need_review": "需人工审核",
    "suggest_reject": "建议驳回",
}


def ai_display_text(value: str | None) -> str | None:
    return AI_DISPLAY_TEXT.get(value, value)


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

        # 解析 AI 管线结果
        import json
        ai_raw = None
        if case.ai_result_json:
            try:
                ai_raw = json.loads(case.ai_result_json)
            except (json.JSONDecodeError, TypeError):
                ai_raw = None

        detection_result = None
        rule_result = None
        ai_review = None
        if ai_raw:
            if ai_raw.get("objects"):
                labels_cn = {
                    "cars": "小汽车", "car": "小汽车", "bus": "公交车",
                    "truck": "卡车", "van": "面包车", "illegal": "违停",
                    "chinese-plate-license": "车牌",
                }
                objects_cn = []
                for o in ai_raw["objects"]:
                    objects_cn.append({
                        "label": labels_cn.get(o.get("label", ""), o.get("label", "")),
                        "confidence": o.get("confidence"),
                        "bbox": o.get("bbox"),
                    })
                detection_result = {
                    "objects": objects_cn,
                    "vehicle_bbox": ai_raw.get("vehicle_bbox"),
                    "plate_bbox": ai_raw.get("plate_bbox"),
                    "model_version": ai_raw.get("model_version"),
                }
            if ai_raw.get("rule_matched") is not None:
                evidence_items = [ai_display_text(e) for e in ai_raw.get("evidence_items", [])]
                missing = [ai_display_text(e) for e in ai_raw.get("missing_evidence", [])]
                rule_result = {
                    "candidate_violation_type": ai_display_text(
                        ai_raw.get("candidate_violation_type", "illegal_stop")
                    ),
                    "rule_code": ai_raw.get("rule_code", "illegal_stop_model"),
                    "rule_matched": ai_raw["rule_matched"],
                    "evidence_level": ai_display_text(ai_raw.get("evidence_level", "")),
                    "evidence_items": evidence_items,
                    "missing_evidence": missing,
                    "reason": ai_raw.get("rule_reason", ""),
                }
            if ai_raw.get("conclusion"):
                ai_review = {
                    "conclusion": ai_display_text(ai_raw["conclusion"]),
                    "ai_confidence": ai_raw.get("ai_confidence"),
                    "reason": ai_raw.get("review_reason", ""),
                    "risk_points": ai_raw.get("risk_points", []),
                    "review_mode": ai_raw.get("review_mode", "text_llm"),
                }

        return {
            "id": case.id, "case_no": case.case_no, "status": case.status,
            "source_type": ev.source_type if ev else None,
            "source_desc": source_desc_map.get(ev.source_type, "") if ev else "",
            "location_text": location_text,
            "captured_at": captured_at,
            "speed": speed,
            "plate_no": case.plate_no,
            "violation_type": ai_display_text(case.violation_type),
            "media": media,
            "detection_result": detection_result,
            "rule_result": rule_result,
            "ai_review": ai_review,
            "review": {"reviewer_id": case.reviewer_id, "review_opinion": case.review_opinion,
                       "reviewed_at": str(case.reviewed_at) if case.reviewed_at else None},
        }
