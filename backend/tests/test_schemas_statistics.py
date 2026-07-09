from app.schemas.statistics import (
    ByLocationItem,
    ByLocationOut,
    ByTimeItem,
    ByTimeOut,
    ByTypeItem,
    ByTypeOut,
    OverviewOut,
    PeriodOut,
)


def test_overview_out_construction():
    o = OverviewOut(
        total_cases=3, approved_count=1, rejected_count=1, pending_count=1,
        approval_rate=33.3, period=PeriodOut(start="s", end="e"),
    )
    assert o.total_cases == 3
    assert o.period.start == "s"


def test_by_location_out():
    o = ByLocationOut(items=[ByLocationItem(location_text="路口A", count=2)])
    assert o.items[0].count == 2


def test_by_type_out():
    o = ByTypeOut(items=[ByTypeItem(violation_type="超速", count=2, percentage=66.7)])
    assert o.items[0].percentage == 66.7


def test_by_time_out():
    o = ByTimeOut(items=[ByTimeItem(date="2026-07-08", count=2)])
    assert o.items[0].date == "2026-07-08"
