from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None = None
    action: str
    target_type: str | None = None
    target_id: int | None = None
    detail: str | None = None
    ip: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
