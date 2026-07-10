from datetime import datetime

from pydantic import BaseModel


class RewardOut(BaseModel):
    id: int
    citizen_id: int
    case_id: int
    violation_id: int | None = None
    amount: int
    reason: str | None = None
    status: str
    paid_at: datetime | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class RewardListResponse(BaseModel):
    items: list[RewardOut]
    total: int
    page: int
    page_size: int
