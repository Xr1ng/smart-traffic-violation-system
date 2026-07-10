# app/schemas/case.py
from pydantic import BaseModel


class CaseListItem(BaseModel):
    id: int
    case_no: str
    status: str
    source_type: str | None = None
    plate_no: str | None = None
    violation_type: str | None = None
    captured_at: str | None = None
    location_text: str | None = None


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    total: int
    page: int
    page_size: int


class CaseDetail(BaseModel):
    id: int
    case_no: str
    status: str
    source_type: str | None = None
    source_desc: str = ""
    location_text: str | None = None
    captured_at: str | None = None
    speed: float | None = None
    plate_no: str | None = None
    violation_type: str | None = None
    media: dict = {}
    detection_result: dict | None = None
    rule_result: dict | None = None
    ai_review: dict | None = None
    review: dict = {}
    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    plate_no: str
    violation_type: str
    fine_amount: int
    points: int
    review_opinion: str


class RejectRequest(BaseModel):
    reject_reason: str


class RecheckResponse(BaseModel):
    message: str
