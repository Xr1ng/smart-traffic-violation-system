from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, model_validator

from app.schemas.statistics import (
    ByLocationItem,
    ByTimeItem,
    ByTypeItem,
    OverviewOut,
    RoadTimeHeatmapItem,
)


class ReportRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_window(self) -> "ReportRequest":
        self.start_time = _as_utc(self.start_time)
        self.end_time = _as_utc(self.end_time)
        if self.start_time > self.end_time:
            raise ValueError("start_time 不能晚于 end_time")
        if self.end_time - self.start_time > timedelta(days=366):
            raise ValueError("报告统计周期不能超过 366 天")
        return self


class ReportStatisticsSnapshot(BaseModel):
    overview: OverviewOut
    trend: list[ByTimeItem] = Field(default_factory=list)
    violation_types: list[ByTypeItem] = Field(default_factory=list)
    locations: list[ByLocationItem] = Field(default_factory=list)
    road_time_hotspots: list[RoadTimeHeatmapItem] = Field(default_factory=list)


class ReportOut(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    summary: str
    trend_analysis: str
    hotspot_analysis: str
    risk_alerts: list[str]
    recommendations: list[str]
    statistics_snapshot: ReportStatisticsSnapshot
    author: str
    generated_at: datetime


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
