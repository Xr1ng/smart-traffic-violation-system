# tests/services/test_intake_service.py
import pytest
from fastapi import HTTPException

from app.services.intake_service import create_intake

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 10


def test_create_intake_citizen(db, citizen_user, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    enqueued = []
    monkeypatch.setattr(
        "app.services.intake_service._enqueue_ai_pipeline",
        lambda case_id, media_url: enqueued.append((case_id, media_url)),
    )
    case = create_intake(
        db,
        source_type="citizen",
        source_id=citizen_user.id,
        image_bytes=JPEG,
        filename="a.jpg",
        location_text="路口A",
    )
    assert case.id is not None
    assert case.case_no.startswith("CASE")
    assert case.status == "uploaded"
    assert case.intake_event.image_hash
    assets = case.intake_event.media_assets
    assert len(assets) == 1
    assert assets[0].asset_type == "original"
    assert enqueued == [(case.id, assets[0].url)]


def test_create_intake_duplicate_rejected(db, citizen_user, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.MEDIA_STORAGE_DIR", str(tmp_path))
    create_intake(
        db, source_type="citizen", source_id=citizen_user.id,
        image_bytes=JPEG, filename="a.jpg", location_text="路口A",
    )
    with pytest.raises(HTTPException) as exc:
        create_intake(
            db, source_type="citizen", source_id=citizen_user.id,
            image_bytes=JPEG, filename="a.jpg", location_text="路口A",
        )
    assert exc.value.status_code == 409
