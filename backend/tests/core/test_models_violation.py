# tests/core/test_models_violation.py
from app.models.violation import (
    AuditLog, Notification, NotificationTemplate, Reward, Vehicle, Violation,
)


def test_create_vehicle(db):
    v = Vehicle(plate_no="粤A12345", owner_id=1, vehicle_type="小汽车", color="白")
    db.add(v); db.commit()
    assert v.id is not None


def test_create_violation_and_notification(db):
    v = Violation(violation_no="VIO20260709000001", case_id=1, plate_no="粤A12345",
                  violation_type="超速", fine_amount=200, points=6)
    db.add(v); db.commit()
    n = Notification(violation_id=v.id, recipient="o@e.com", content="x", status="pending", provider="email")
    db.add(n); db.commit()
    t = NotificationTemplate(code="violation_notice", subject_template="s", body_template="b")
    db.add(t); db.commit()
    r = Reward(citizen_id=1, case_id=1, violation_id=v.id, amount=10, reason="举报成立")
    db.add(r); db.commit()
    a = AuditLog(actor_id=1, action="approve", target_type="case", target_id=1, detail="ok")
    db.add(a); db.commit()
    assert all(x.id is not None for x in [v, n, t, r, a])
