# app/api/v1/violations.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.violation import ViolationListResponse, ViolationOut
from app.services.violation_service import ViolationService

router = APIRouter(tags=["violations"])


@router.get("/violations", response_model=ViolationListResponse)
def list_violations(plate_no: str | None = None, violation_type: str | None = None,
                    status: str | None = None,
                    start_time: datetime | None = None, end_time: datetime | None = None,
                    location_text: str | None = None,
                    page: int = Query(1, ge=1),
                    page_size: int = Query(20, ge=1, le=100),
                    db: Session = Depends(get_db),
                    user: User = Depends(require_role("reviewer", "admin"))) -> ViolationListResponse:
    res = ViolationService(db).list_violations(
        plate_no=plate_no, violation_type=violation_type, status=status,
        start_time=start_time, end_time=end_time, location_text=location_text,
        page=page, page_size=page_size)
    return ViolationListResponse(items=[ViolationOut.model_validate(v) for v in res["items"]],
                                 total=res["total"], page=res["page"], page_size=res["page_size"])


@router.get("/violations/{violation_id}", response_model=ViolationOut)
def get_violation(violation_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_role("reviewer", "admin"))) -> ViolationOut:
    v = ViolationService(db).get_violation(violation_id)
    if v is None:
        raise HTTPException(status_code=404, detail="违章不存在")
    return ViolationOut.model_validate(v)


@router.get("/owners/{owner_id}/violations", response_model=ViolationListResponse)
def owner_violations(owner_id: int, page: int = Query(1, ge=1),
                     page_size: int = Query(20, ge=1, le=100),
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)) -> ViolationListResponse:
    if user.role.code == "citizen" and user.id != owner_id:
        raise HTTPException(status_code=403, detail="无权查看他人违章")
    res = ViolationService(db).list_by_owner(owner_id, page=page, page_size=page_size)
    return ViolationListResponse(items=[ViolationOut.model_validate(v) for v in res["items"]],
                                 total=res["total"], page=res["page"], page_size=res["page_size"])
