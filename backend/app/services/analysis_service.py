from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.adapters.base import LLMProvider
from app.schemas.report import ReportOut, ReportStatisticsSnapshot
from app.services.statistics_service import StatisticsService


class AnalysisService:
    def __init__(self, db: Session, provider: LLMProvider) -> None:
        self.db = db
        self.provider = provider

    def generate_report(self, start_time: datetime, end_time: datetime) -> ReportOut:
        start_iso = start_time.isoformat()
        end_iso = end_time.isoformat()
        statistics = StatisticsService(self.db)
        heatmap = statistics.road_time_heatmap(start_iso, end_iso)
        hotspots = sorted(
            (item for item in heatmap.items if item.count > 0),
            key=lambda item: (-item.count, item.road, item.time_slot),
        )[:20]
        violation_types = sorted(
            statistics.by_type(start_iso, end_iso).items,
            key=lambda item: (-item.value, item.name),
        )
        snapshot = ReportStatisticsSnapshot(
            overview=statistics.overview(start_iso, end_iso),
            trend=statistics.by_time(start_iso, end_iso).items,
            violation_types=violation_types,
            locations=statistics.by_location(start_iso, end_iso, 10).items,
            road_time_hotspots=hotspots,
        )
        narrative = self.provider.generate_report(snapshot.model_dump(mode="json"))

        return ReportOut(
            title="交通违章综合分析报告",
            start_time=start_time,
            end_time=end_time,
            summary=narrative.summary,
            trend_analysis=narrative.trend_analysis,
            hotspot_analysis=narrative.hotspot_analysis,
            risk_alerts=narrative.risk_alerts,
            recommendations=narrative.recommendations,
            statistics_snapshot=snapshot,
            author="AI 分析助手",
            generated_at=datetime.now(timezone.utc),
        )
