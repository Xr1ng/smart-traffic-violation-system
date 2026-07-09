# app/schemas/case.py
from pydantic import BaseModel


class CaseListItem(BaseModel):
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
    plate_no: str | None = None
    violation_type: str | None = None
    intake_event: dict
    media: list[dict]
    ai_detection_result: dict | None = None
    violation_rule_result: dict | None = None
    ai_review_result: dict | None = None
    review: dict


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
