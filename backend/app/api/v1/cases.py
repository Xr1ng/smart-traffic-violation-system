# app/api/v1/cases.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_notification_provider, require_role
from app.models.user import User
from app.models.violation import Reward
from app.schemas.case import (
    ApproveRequest, CaseDetail, CaseListResponse, CaseListItem, RejectRequest, RecheckResponse,
)
from app.services.case_service import CaseService, ai_display_text
from app.services.notification_provider import NotificationProvider
from app.services.review_service import ReviewService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=CaseListResponse)
def list_cases(status: str | None = None, source_type: str | None = None,
               location_text: str | None = None, plate_no: str | None = None,
               keyword: str | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db),
               user: User = Depends(require_role("citizen", "reviewer", "admin"))) -> CaseListResponse:
    res = CaseService(db).list_cases(
        user=user, status=status, source_type=source_type,
        location_text=location_text, plate_no=plate_no, keyword=keyword,
        page=page, page_size=page_size)
    case_ids = [case.id for case in res["items"]]
    rewards = (
        db.query(Reward).filter(Reward.case_id.in_(case_ids)).all()
        if case_ids
        else []
    )
    reward_by_case = {reward.case_id: reward.amount for reward in rewards}
    source_desc_map = {"citizen": "市民举报", "camera": "摄像头抓拍", "admin": "后台上传"}
    items = []
    for c in res["items"]:
        ev = c.intake_event
        media = {}
        if ev:
            original = next(
                (asset for asset in ev.media_assets if asset.asset_type == "original"),
                None,
            )
            if original:
                media["original_url"] = original.url
        # 解析 AI 结果用于卡片展示
        ai_review = None
        if c.ai_result_json:
            try:
                import json
                ai_raw = json.loads(c.ai_result_json)
                if ai_raw.get("conclusion"):
                    cn_map = {"suggest_approve": "建议通过", "need_review": "需人工审核", "suggest_reject": "建议驳回"}
                    ai_review = {
                        "conclusion": cn_map.get(ai_raw["conclusion"], ai_raw["conclusion"]),
                        "ai_confidence": ai_raw.get("ai_confidence"),
                    }
            except (json.JSONDecodeError, TypeError):
                pass
        items.append(CaseListItem(
            id=c.id,
            case_no=c.case_no, status=c.status,
            source_type=ev.source_type if ev else None,
            source_desc=source_desc_map.get(ev.source_type, "") if ev else "",
            description=ev.description if ev else None,
            plate_no=c.plate_no, violation_type=ai_display_text(c.violation_type),
            captured_at=str(ev.captured_at) if ev and ev.captured_at else None,
            location_text=ev.location_text if ev else None,
            media=media,
            reward=reward_by_case.get(c.id),
            ai_review=ai_review,
        ))
    return CaseListResponse(items=items, total=res["total"], page=res["page"], page_size=res["page_size"])


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db),
             user: User = Depends(require_role("citizen", "reviewer", "admin"))) -> CaseDetail:
    return CaseDetail(**CaseService(db).get_case_detail(case_id, user=user))


@router.post("/{case_id}/approve")
def approve(case_id: int, body: ApproveRequest, db: Session = Depends(get_db),
            user: User = Depends(require_role("reviewer", "admin")),
            provider: NotificationProvider = Depends(get_notification_provider)) -> dict:
    return ReviewService(db, provider).approve(
        case_id, user, plate_no=body.plate_no, violation_type=body.violation_type,
        fine_amount=body.fine_amount, points=body.points, review_opinion=body.review_opinion)


@router.post("/{case_id}/reject")
def reject(case_id: int, body: RejectRequest, db: Session = Depends(get_db),
           user: User = Depends(require_role("reviewer", "admin")),
           provider: NotificationProvider = Depends(get_notification_provider)) -> dict:
    return ReviewService(db, provider).reject(case_id, user, reject_reason=body.reject_reason)


@router.post("/{case_id}/request-recheck", response_model=RecheckResponse, status_code=202)
def request_recheck(case_id: int, db: Session = Depends(get_db),
                    user: User = Depends(require_role("reviewer", "admin")),
                    provider: NotificationProvider = Depends(get_notification_provider)) -> RecheckResponse:
    return RecheckResponse(**ReviewService(db, provider).request_recheck(case_id, user))
