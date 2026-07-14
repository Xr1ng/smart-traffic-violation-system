import json
from datetime import datetime, timezone

import pytest

from app.schemas.report import ReportOut
from app.schemas.statistics import (
    ByLocationItem,
    ByTimeItem,
    ByTypeItem,
    OverviewOut,
    RoadTimeHeatmapItem,
)
from app.services.report_storage import ReportStorageError, ReportStorageService


def make_report(
    *,
    start: str = "2026-06-30T16:00:00Z",
    end: str = "2026-07-31T15:59:59Z",
    generated: str = "2026-07-14T02:30:00Z",
) -> ReportOut:
    return ReportOut(
        title="交通违章综合分析报告",
        start_time=datetime.fromisoformat(start.replace("Z", "+00:00")),
        end_time=datetime.fromisoformat(end.replace("Z", "+00:00")),
        summary="本期共发现 12 起违章。\n整体风险可控。",
        trend_analysis="违章数量先升后降。",
        hotspot_analysis="人民路晚高峰较集中。",
        risk_alerts=["晚高峰风险", "学校周边风险"],
        recommendations=["加强巡查", "优化信号灯配时"],
        statistics_snapshot={
            "overview": OverviewOut(
                total_cases=15,
                total_violations=12,
                approve_rate=80,
                reject_rate=20,
                pending_count=1,
            ),
            "trend": [ByTimeItem(date="2026-07-01", count=2)],
            "violation_types": [ByTypeItem(name="违法停车", value=8, percentage=66.7)],
            "locations": [ByLocationItem(name="人民路", value=5)],
            "road_time_hotspots": [
                RoadTimeHeatmapItem(road="人民路", time_slot="17-19", count=5),
            ],
        },
        author="AI 分析助手",
        generated_at=datetime.fromisoformat(generated.replace("Z", "+00:00")),
    )


def test_save_writes_versioned_markdown_and_round_trips_report(tmp_path):
    storage = ReportStorageService(tmp_path)

    saved = storage.save(make_report())

    assert len(saved.id) == 12
    assert saved.id.isalnum()
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == (
        f"2026-07-01_2026-07-31_20260714T023000Z_{saved.id}.md"
    )
    content = files[0].read_text(encoding="utf-8")
    assert content.startswith("<!-- traffic-report-meta:v1\n")
    assert "# 交通违章综合分析报告" in content
    assert "## 01 执行摘要" in content
    assert "整体风险可控" in content
    assert storage.get(saved.id) == saved

    metadata_text = content.split("\n-->", 1)[0].split("\n", 1)[1]
    assert json.loads(metadata_text)["report"]["summary"].startswith("本期共发现")


def test_save_keeps_unique_versions_for_the_same_period(tmp_path):
    storage = ReportStorageService(tmp_path)

    first = storage.save(make_report())
    second = storage.save(make_report())

    assert first.id != second.id
    assert len(list(tmp_path.glob("*.md"))) == 2


def test_list_returns_empty_page_when_storage_directory_is_missing(tmp_path):
    storage = ReportStorageService(tmp_path / "not-created")

    result = storage.list(page=1, page_size=20)

    assert result.total == 0
    assert result.items == []
    assert not (tmp_path / "not-created").exists()


def test_list_sorts_paginates_and_filters_by_overlapping_period(tmp_path):
    storage = ReportStorageService(tmp_path)
    july = storage.save(make_report(generated="2026-07-14T02:00:00Z"))
    august = storage.save(make_report(
        start="2026-07-31T16:00:00Z",
        end="2026-08-31T15:59:59Z",
        generated="2026-08-14T02:00:00Z",
    ))
    september = storage.save(make_report(
        start="2026-08-31T16:00:00Z",
        end="2026-09-30T15:59:59Z",
        generated="2026-09-14T02:00:00Z",
    ))

    first_page = storage.list(page=1, page_size=2)
    overlap = storage.list(
        page=1,
        page_size=20,
        start_time=datetime(2026, 7, 31, tzinfo=timezone.utc),
        end_time=datetime(2026, 8, 1, tzinfo=timezone.utc),
    )

    assert first_page.total == 3
    assert [item.id for item in first_page.items] == [september.id, august.id]
    assert [item.id for item in overlap.items] == [august.id, july.id]


def test_list_skips_corrupt_markdown_but_get_reports_damage(tmp_path, caplog):
    storage = ReportStorageService(tmp_path)
    saved = storage.save(make_report())
    file_path = next(tmp_path.glob(f"*_{saved.id}.md"))
    file_path.write_text("not a report", encoding="utf-8")

    result = storage.list(page=1, page_size=20)

    assert result.total == 0
    assert "Skipping invalid report file" in caplog.text
    with pytest.raises(ReportStorageError, match="文件损坏"):
        storage.get(saved.id)


def test_get_rejects_invalid_or_missing_report_ids(tmp_path):
    storage = ReportStorageService(tmp_path)

    with pytest.raises(FileNotFoundError):
        storage.get("../outside")
    with pytest.raises(FileNotFoundError):
        storage.get("0123456789ab")


def test_save_failure_removes_temporary_file(tmp_path, monkeypatch):
    storage = ReportStorageService(tmp_path)

    def fail_replace(_source, _target):
        raise OSError("disk unavailable")

    monkeypatch.setattr("app.services.report_storage.os.replace", fail_replace)

    with pytest.raises(ReportStorageError, match="保存失败"):
        storage.save(make_report())

    assert list(tmp_path.glob("*.tmp")) == []
    assert list(tmp_path.glob("*.md")) == []
