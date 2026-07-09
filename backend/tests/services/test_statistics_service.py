from datetime import datetime, timezone

from app.models.intake import Case, IntakeEvent
from app.models.violation import Violation
from app.services.statistics_service import StatisticsService

WIN = ("2000-01-01T00:00:00", "2099-01-01T00:00:00")  # 宽窗，覆盖所有种子


def _seed_case(db, *, status, created_at, case_no):
    ev = IntakeEvent(source_type="admin", image_hash="h" * 8)
    db.add(ev)
    db.flush()
    c = Case(case_no=case_no, intake_event_id=ev.id, status=status, created_at=created_at)
    db.add(c)
    db.commit()
    return c


def _seed_violation(db, *, case, violation_type, location_text, created_at, vio_no):
    v = Violation(
        violation_no=vio_no, case_id=case.id, plate_no="京A1", violation_type=violation_type,
        location_text=location_text, fine_amount=200, points=3, status="pending",
        created_at=created_at,
    )
    db.add(v)
    db.commit()
    return v


def test_overview_counts(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_case(db, status="rejected", created_at=t, case_no="C2")
    _seed_case(db, status="pending_human_review", created_at=t, case_no="C3")
    out = StatisticsService(db).overview(*WIN)
    assert out.total_cases == 3
    assert out.approved_count == 1
    assert out.rejected_count == 1
    assert out.pending_count == 1
    assert out.approval_rate == round(1 / 3 * 100, 1)


def test_by_location_orders_desc_and_limit(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口A", created_at=t, vio_no="V2")
    _seed_violation(db, case=c, violation_type="超速", location_text="路口B", created_at=t, vio_no="V3")
    out = StatisticsService(db).by_location(*WIN, limit=10)
    assert out.items[0].location_text == "路口A"
    assert out.items[0].count == 2
    out_limit1 = StatisticsService(db).by_location(*WIN, limit=1)
    assert len(out_limit1.items) == 1


def test_by_type_percentage(db):
    t = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t, vio_no="V2")
    _seed_violation(db, case=c, violation_type="违停", location_text="A", created_at=t, vio_no="V3")
    out = StatisticsService(db).by_type(*WIN)
    assert len(out.items) == 2
    super_item = next(i for i in out.items if i.violation_type == "超速")
    assert super_item.count == 2
    assert super_item.percentage == round(2 / 3 * 100, 1)


def test_by_time_daily_grouping(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 9, 11, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V2")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t2, vio_no="V3")
    out = StatisticsService(db).by_time(*WIN)
    assert len(out.items) == 2
    assert out.items[0].date == "2026-07-08"
    assert out.items[0].count == 2
    assert out.items[1].date == "2026-07-09"
    assert out.items[1].count == 1


def test_overview_time_window_excludes_outside(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
    _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_case(db, status="approved", created_at=t2, case_no="C2")
    # 窄窗只含 t2
    out = StatisticsService(db).overview("2026-07-09T00:00:00", "2026-07-11T00:00:00")
    assert out.total_cases == 1
    assert out.approved_count == 1


def test_by_type_time_window_excludes_outside(db):
    t1 = datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc)
    c = _seed_case(db, status="approved", created_at=t1, case_no="C1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t1, vio_no="V1")
    _seed_violation(db, case=c, violation_type="超速", location_text="A", created_at=t2, vio_no="V2")
    out = StatisticsService(db).by_type("2026-07-09T00:00:00", "2026-07-11T00:00:00")
    assert len(out.items) == 1
    assert out.items[0].count == 1
