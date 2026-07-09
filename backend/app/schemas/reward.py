from datetime import datetime

from pydantic import BaseModel


class RewardOut(BaseModel):
    id: int
    citizen_id: int
    case_id: int
    violation_id: int | None
    amount: int
    reason: str | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class RewardListResponse(BaseModel):
    items: list[RewardOut]
    total: int
    page: int
    page_size: int
