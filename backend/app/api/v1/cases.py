# app/api/v1/cases.py
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_notification_provider, require_role
from app.models.user import User
from app.schemas.case import (
    ApproveRequest, CaseDetail, CaseListResponse, CaseListItem, RejectRequest, RecheckResponse,
)
from app.services.case_service import CaseService
from app.services.notification_provider import EmailSmtpProvider, NotificationProvider
from app.services.review_service import ReviewService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=CaseListResponse)
def list_cases(status: str | None = None, source_type: str | None = None,
               location_text: str | None = None, plate_no: str | None = None,
               start_time: datetime | None = None, end_time: datetime | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db),
               user: User = Depends(require_role("citizen", "reviewer", "admin"))) -> CaseListResponse:
    res = CaseService(db).list_cases(
        user=user, status=status, source_type=source_type,
        location_text=location_text, plate_no=plate_no,
        start_time=start_time, end_time=end_time, page=page, page_size=page_size)
    items = []
    for c in res["items"]:
        ev = c.intake_event
        items.append(CaseListItem(
            id=c.id, case_no=c.case_no, status=c.status,
            source_type=ev.source_type if ev else None,
            plate_no=c.plate_no, violation_type=c.violation_type,
            captured_at=str(ev.captured_at) if ev and ev.captured_at else None,
            location_text=ev.location_text if ev else None,
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
           user: User = Depends(require_role("reviewer", "admin"))) -> dict:
    return ReviewService(db, EmailSmtpProvider()).reject(case_id, user, reject_reason=body.reject_reason)


@router.post("/{case_id}/request-recheck", response_model=RecheckResponse, status_code=202)
def request_recheck(case_id: int, db: Session = Depends(get_db),
                    user: User = Depends(require_role("reviewer", "admin"))) -> RecheckResponse:
    return RecheckResponse(**ReviewService(db, EmailSmtpProvider()).request_recheck(case_id, user))
