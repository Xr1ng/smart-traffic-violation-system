from pydantic import BaseModel


class OverviewOut(BaseModel):
    total_cases: int
    total_violations: int
    total_reports: int = 0
    approve_rate: float
    reject_rate: float
    pending_count: int
    today_new: int = 0
    notify_success_rate: float = 0.0


class ByLocationItem(BaseModel):
    name: str | None
    value: int


class ByLocationOut(BaseModel):
    items: list[ByLocationItem]


class ByTypeItem(BaseModel):
    name: str
    value: int
    percentage: float = 0.0


class ByTypeOut(BaseModel):
    items: list[ByTypeItem]


class ByTimeItem(BaseModel):
    date: str
    count: int


class ByTimeOut(BaseModel):
    items: list[ByTimeItem]
