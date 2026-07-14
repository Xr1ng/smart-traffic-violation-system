from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreateIn,
    AnnouncementListResponse,
    AnnouncementOut,
    AnnouncementUpdateIn,
)
from app.services.announcement_service import AnnouncementService

_admin_required = require_role("admin")

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
    dependencies=[Depends(get_current_user)],
)
admin_router = APIRouter(
    prefix="/admin/announcements",
    tags=["announcements"],
    dependencies=[Depends(_admin_required)],
)


@router.get("", response_model=AnnouncementListResponse)
def list_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AnnouncementListResponse:
    result = AnnouncementService(db).list_announcements(
        page=page, page_size=page_size
    )
    return AnnouncementListResponse(
        items=[AnnouncementOut.model_validate(item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/{announcement_id}", response_model=AnnouncementOut)
def get_announcement(
    announcement_id: int, db: Session = Depends(get_db)
) -> AnnouncementOut:
    announcement = AnnouncementService(db).get(announcement_id)
    return AnnouncementOut.model_validate(announcement)


@admin_router.post("", response_model=AnnouncementOut, status_code=201)
def create_announcement(
    body: AnnouncementCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(_admin_required),
) -> AnnouncementOut:
    announcement = AnnouncementService(db).create(
        title=body.title,
        content=body.content,
        actor_id=current_user.id,
    )
    return AnnouncementOut.model_validate(announcement)


@admin_router.patch("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: int,
    body: AnnouncementUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(_admin_required),
) -> AnnouncementOut:
    announcement = AnnouncementService(db).update(
        announcement_id,
        title=body.title,
        content=body.content,
        actor_id=current_user.id,
    )
    return AnnouncementOut.model_validate(announcement)


@admin_router.delete("/{announcement_id}", status_code=204)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_admin_required),
) -> Response:
    AnnouncementService(db).delete(announcement_id, actor_id=current_user.id)
    return Response(status_code=204)
