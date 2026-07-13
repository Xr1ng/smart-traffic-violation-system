# app/services/intake_service.py
import threading
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.intake import Case, IntakeEvent, MediaAsset
from app.services.image_hash import compute_image_hash
from app.services.image_validate import validate_image
from app.services.storage import save_media


def _gen_case_no(case_id: int) -> str:
    return f"CASE{datetime.now(timezone.utc):%Y%m%d}{case_id:06d}"


def _run_ai_async(case_id: int, media_url: str):
    """在独立线程+独立 DB session 中跑 AI 管线，不阻塞上传响应。"""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.core.db import SessionLocal
        from app.services.ai_pipeline import run_ai_pipeline

        db2 = SessionLocal()
        try:
            case = db2.get(Case, case_id)
            if case is None:
                logger.warning("AI async: case %s not found", case_id)
                return
            run_ai_pipeline(case, media_url)
        finally:
            db2.close()
    except Exception:
        logger.exception("AI async failed for case %s", case_id)


def _enqueue_ai_pipeline(case_id: int, media_url: str) -> None:
    threading.Thread(target=_run_ai_async, args=(case_id, media_url), daemon=True).start()


def create_intake(
    db: Session,
    *,
    source_type: str,
    source_id: int | None,
    image_bytes: bytes,
    filename: str,
    location_text: str | None,
    description: str | None = None,
    captured_at: datetime | None = None,
    speed: float | None = None,
    longitude: float | None = None,
    latitude: float | None = None,
) -> Case:
    mime = validate_image(image_bytes, filename)
    image_hash = compute_image_hash(image_bytes)

    existing = db.query(IntakeEvent).filter(IntakeEvent.image_hash == image_hash).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="重复举报，该图片已存在")

    url, _ext = save_media(image_bytes, mime)

    event = IntakeEvent(
        source_type=source_type,
        source_id=source_id,
        location_text=location_text,
        description=description,
        longitude=longitude,
        latitude=latitude,
        captured_at=captured_at,
        speed=speed,
        image_hash=image_hash,
        status="uploaded",
    )
    db.add(event)
    db.flush()  # 拿 event.id

    db.add(MediaAsset(
        intake_event_id=event.id,
        asset_type="original",
        url=url,
        mime_type=mime,
        size=len(image_bytes),
    ))

    case = Case(case_no="placeholder", intake_event_id=event.id, status="uploaded")
    db.add(case)
    db.flush()
    case.case_no = _gen_case_no(case.id)
    db.commit()
    db.refresh(case)

    # AI 管线在后台线程异步跑，不阻塞上传响应
    _enqueue_ai_pipeline(case.id, url)

    return case
