from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.report import ReportRequest


def test_report_request_accepts_a_366_day_window():
    request = ReportRequest(
        start_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert (request.end_time - request.start_time).days == 366


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [
        ("2026-07-02T00:00:00Z", "2026-07-01T00:00:00Z"),
        ("2025-01-01T00:00:00Z", "2026-01-03T00:00:00Z"),
    ],
)
def test_report_request_rejects_invalid_windows(start_time, end_time):
    with pytest.raises(ValidationError):
        ReportRequest(start_time=start_time, end_time=end_time)
