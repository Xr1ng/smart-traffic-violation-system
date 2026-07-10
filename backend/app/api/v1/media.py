from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import require_role
from app.models.intake import MediaAsset
from app.models.user import User

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{filename}", response_class=FileResponse)
def get_media(
    filename: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("citizen", "reviewer", "admin")),
) -> FileResponse:
    if filename in {".", ".."} or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=404, detail="Media file not found")

    asset = db.query(MediaAsset).filter(MediaAsset.url == f"/media/{filename}").first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Media file not found")

    event = asset.intake_event
    if user.role.code == "citizen" and not (
        event.source_type == "citizen" and event.source_id == user.id
    ):
        raise HTTPException(status_code=403, detail="无权查看该媒体")

    storage_root = Path(settings.MEDIA_STORAGE_DIR).resolve()
    media_path = (storage_root / filename).resolve()
    if media_path.parent != storage_root or not media_path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found")
    return FileResponse(media_path)
