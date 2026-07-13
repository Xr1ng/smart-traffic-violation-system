from datetime import datetime, timezone

from app.ai.adapters.base import ReportNarrativeData
from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation
from app.services.analysis_service import AnalysisService


class FakeReportProvider:
    def __init__(self):
        self.payload = None

    def generate_report(self, payload):
        self.payload = payload
        return ReportNarrativeData(
            summary="本期报告摘要",
            trend_analysis="趋势分析",
            hotspot_analysis="热点分析",
            risk_alerts=["风险一"],
            recommendations=["建议一"],
        )


def test_analysis_service_builds_aggregate_only_snapshot(db):
    moment = datetime(2026, 7, 8, 18, 0, tzinfo=timezone.utc)
    event = IntakeEvent(source_type="admin", image_hash="report-hash")
    db.add(event)
    db.flush()
    case = Case(
        case_no="REPORT-CASE-1",
        intake_event_id=event.id,
        status="approved",
        created_at=moment,
    )
    db.add(case)
    db.flush()
    db.add(Violation(
        violation_no="REPORT-V-1",
        case_id=case.id,
        plate_no="粤A12345",
        violation_type="违法停车",
        occurred_at=moment,
        location_text="人民路",
        fine_amount=200,
        points=3,
        status="pending",
        created_at=moment,
    ))
    db.commit()
    provider = FakeReportProvider()

    report = AnalysisService(db, provider).generate_report(
        datetime(2026, 7, 1, tzinfo=timezone.utc),
        datetime(2026, 7, 31, 23, 59, tzinfo=timezone.utc),
    )

    assert report.summary == "本期报告摘要"
    assert report.statistics_snapshot.overview.total_violations == 1
    assert report.statistics_snapshot.locations[0].name == "人民路"
    assert report.statistics_snapshot.road_time_hotspots[0].time_slot == "17-19"
    assert provider.payload == report.statistics_snapshot.model_dump(mode="json")
    assert "粤A12345" not in str(provider.payload)


def test_analysis_service_limits_and_orders_heatmap_hotspots(db, monkeypatch):
    provider = FakeReportProvider()

    class FakeStatisticsService:
        def __init__(self, _db):
            pass

        def overview(self, *_args):
            from app.schemas.statistics import OverviewOut
            return OverviewOut(
                total_cases=0, total_violations=0, approve_rate=0,
                reject_rate=0, pending_count=0,
            )

        def by_time(self, *_args):
            from app.schemas.statistics import ByTimeOut
            return ByTimeOut(items=[])

        def by_type(self, *_args):
            from app.schemas.statistics import ByTypeOut
            return ByTypeOut(items=[])

        def by_location(self, *_args, **_kwargs):
            from app.schemas.statistics import ByLocationOut
            return ByLocationOut(items=[])

        def road_time_heatmap(self, *_args):
            from app.schemas.statistics import RoadTimeHeatmapItem, RoadTimeHeatmapOut
            items = [
                RoadTimeHeatmapItem(road=f"路段{i}", time_slot="7-9", count=i)
                for i in range(25)
            ]
            return RoadTimeHeatmapOut(time_slots=["7-9"], roads=[], items=items)

    monkeypatch.setattr("app.services.analysis_service.StatisticsService", FakeStatisticsService)

    report = AnalysisService(db, provider).generate_report(
        datetime(2026, 7, 1, tzinfo=timezone.utc),
        datetime(2026, 7, 2, tzinfo=timezone.utc),
    )

    hotspots = report.statistics_snapshot.road_time_hotspots
    assert len(hotspots) == 20
    assert [item.count for item in hotspots] == list(range(24, 4, -1))
