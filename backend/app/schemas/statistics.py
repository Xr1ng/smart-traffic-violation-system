from pydantic import BaseModel


class PeriodOut(BaseModel):
    start: str | None
    end: str | None


class OverviewOut(BaseModel):
    total_cases: int
    approved_count: int
    rejected_count: int
    pending_count: int
    approval_rate: float
    period: PeriodOut


class ByLocationItem(BaseModel):
    location_text: str | None
    count: int


class ByLocationOut(BaseModel):
    items: list[ByLocationItem]


class ByTypeItem(BaseModel):
    violation_type: str
    count: int
    percentage: float


class ByTypeOut(BaseModel):
    items: list[ByTypeItem]


class ByTimeItem(BaseModel):
    date: str
    count: int


class ByTimeOut(BaseModel):
    items: list[ByTimeItem]
