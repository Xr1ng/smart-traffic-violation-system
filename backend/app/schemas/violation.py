# app/schemas/violation.py
from pydantic import BaseModel


class ViolationOut(BaseModel):
    id: int
    violation_no: str
    case_id: int
    plate_no: str
    violation_type: str
    fine_amount: int
    points: int
    status: str
    occurred_at: str | None = None
    location_text: str | None = None

    model_config = {"from_attributes": True}


class ViolationListResponse(BaseModel):
    items: list[ViolationOut]
    total: int
    page: int
    page_size: int
