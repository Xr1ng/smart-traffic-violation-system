from datetime import datetime, timezone

from app.schemas.report import ReportOut, ReportStatisticsSnapshot
from app.schemas.statistics import OverviewOut
from app.tasks.report_task import generate_report_task


def test_generate_report_task_saves_closes_session_and_returns_json(monkeypatch):
    session = type(
        "Session",
        (),
        {"closed": False, "close": lambda self: setattr(self, "closed", True)},
    )()
    provider = object()

    class FakeAnalysisService:
        def __init__(self, received_session, received_provider):
            assert received_session is session
            assert received_provider is provider

        def generate_report(self, start_time, end_time):
            return ReportOut(
                title="交通违章综合分析报告",
                start_time=start_time,
                end_time=end_time,
                summary="摘要",
                trend_analysis="趋势",
                hotspot_analysis="热点",
                risk_alerts=[],
                recommendations=["建议"],
                statistics_snapshot=ReportStatisticsSnapshot(
                    overview=OverviewOut(
                        total_cases=0,
                        total_violations=0,
                        approve_rate=0,
                        reject_rate=0,
                        pending_count=0,
                    ),
                ),
                author="AI 分析助手",
                generated_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            )

    class FakeReportStorageService:
        def __init__(self, directory):
            assert directory == "test-reports"

        def save(self, report):
            from app.schemas.report import SavedReportOut

            return SavedReportOut(id="abcdef123456", **report.model_dump())

    monkeypatch.setattr("app.tasks.report_task.SessionLocal", lambda: session)
    monkeypatch.setattr("app.tasks.report_task.get_llm_provider", lambda: provider)
    monkeypatch.setattr("app.tasks.report_task.AnalysisService", FakeAnalysisService)
    monkeypatch.setattr("app.tasks.report_task.ReportStorageService", FakeReportStorageService)
    monkeypatch.setattr("app.tasks.report_task.settings.REPORT_STORAGE_DIR", "test-reports")

    result = generate_report_task.run(
        "2026-07-01T00:00:00Z", "2026-07-31T23:59:59Z",
    )

    assert result["summary"] == "摘要"
    assert result["id"] == "abcdef123456"
    assert result["generated_at"] == "2026-07-13T00:00:00Z"
    assert session.closed is True
