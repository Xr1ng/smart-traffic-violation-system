# app/api/v1/intakes.py
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_camera_device, require_role
from app.models.intake import CameraDevice
from app.models.user import User
from app.schemas.intake import IntakeResponse
from app.services.intake_service import create_intake

router = APIRouter(prefix="/intakes", tags=["intakes"])


def _to_response(case) -> IntakeResponse:
    return IntakeResponse(case_id=case.id, case_no=case.case_no, status=case.status, message="图片已接收，等待处理")


@router.post("/citizen-reports", response_model=IntakeResponse)
def citizen_report(
    image: UploadFile = File(...),
    location_text: str = Form(None),
    captured_at: datetime | None = Form(None),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("citizen")),
) -> IntakeResponse:
    data = image.file.read()
    case = create_intake(
        db, source_type="citizen", source_id=user.id,
        image_bytes=data, filename=image.filename or "upload.jpg",
        location_text=location_text,
        captured_at=captured_at,
        description=description,
    )
    return _to_response(case)


@router.post("/admin-uploads", response_model=IntakeResponse)
def admin_upload(
    image: UploadFile = File(...),
    location_text: str = Form(None),
    captured_at: datetime | None = Form(None),
    speed: float | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("reviewer", "admin")),
) -> IntakeResponse:
    data = image.file.read()
    case = create_intake(
        db, source_type="admin", source_id=user.id,
        image_bytes=data, filename=image.filename or "upload.jpg",
        location_text=location_text,
        captured_at=captured_at,
        speed=speed,
    )
    return _to_response(case)


@router.post("/camera-captures", response_model=IntakeResponse)
def camera_capture(
    image: UploadFile = File(...),
    location_text: str = Form(None),
    speed: float | None = Form(None),
    db: Session = Depends(get_db),
    device: CameraDevice = Depends(get_camera_device),
) -> IntakeResponse:
    data = image.file.read()
    case = create_intake(
        db, source_type="camera", source_id=device.id,
        image_bytes=data, filename=image.filename or "capture.jpg",
        location_text=location_text or device.location_text,
        speed=speed,
    )
    return _to_response(case)
