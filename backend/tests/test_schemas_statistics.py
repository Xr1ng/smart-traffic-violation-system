from app.schemas.statistics import (
    ByLocationItem,
    ByLocationOut,
    ByTimeItem,
    ByTimeOut,
    ByTypeItem,
    ByTypeOut,
    OverviewOut,
)


def test_overview_out_construction():
    o = OverviewOut(
        total_cases=3, total_violations=1, approve_rate=33.3,
        reject_rate=33.3, pending_count=1,
    )
    assert o.total_cases == 3
    assert o.approve_rate == 33.3


def test_by_location_out():
    o = ByLocationOut(items=[ByLocationItem(name="路口A", value=2)])
    assert o.items[0].value == 2


def test_by_type_out():
    o = ByTypeOut(items=[ByTypeItem(name="超速", value=2, percentage=66.7)])
    assert o.items[0].percentage == 66.7


def test_by_time_out():
    o = ByTimeOut(items=[ByTimeItem(date="2026-07-08", count=2)])
    assert o.items[0].date == "2026-07-08"
