# tests/services/test_review_service.py
import pytest
from fastapi import HTTPException

from app.models.user import Role, User
from app.models.violation import Vehicle
from app.services.notification_provider import FakeNotificationProvider
from app.services.review_service import ReviewService


def test_approve_citizen_case_creates_violation_reward_notification(db, citizen_user, reviewer_user, pending_case):
    veh = Vehicle(plate_no="粤A12345", owner_id=citizen_user.id, vehicle_type="小汽车"); db.add(veh); db.commit()
    from app.models.violation import NotificationTemplate
    db.add(NotificationTemplate(code="violation_notice", subject_template="s", body_template="b")); db.commit()
    svc = ReviewService(db, FakeNotificationProvider())
    res = svc.approve(pending_case.id, reviewer_user, plate_no="粤A12345", violation_type="超速",
                      fine_amount=200, points=6, review_opinion="证据清晰")
    assert res["violation_no"].startswith("VIO")
    assert res["notification_status"] == "sent"
    assert res["reward_id"] is not None
    from app.models.intake import Case
    assert db.get(Case, pending_case.id).status == "notified"


def test_approve_missing_plate_400(db, reviewer_user, pending_case):
    svc = ReviewService(db, FakeNotificationProvider())
    with pytest.raises(HTTPException) as exc:
        svc.approve(pending_case.id, reviewer_user, plate_no="", violation_type="超速",
                    fine_amount=200, points=6, review_opinion="x")
    assert exc.value.status_code == 400


def test_approve_wrong_state_409(db, reviewer_user, citizen_user):
    from app.models.intake import Case, IntakeEvent
    ev = IntakeEvent(source_type="citizen", source_id=citizen_user.id, image_hash="up1"); db.add(ev); db.flush()
    case = Case(case_no="CASE-UP-1", intake_event_id=ev.id, status="uploaded"); db.add(case); db.commit()
    svc = ReviewService(db, FakeNotificationProvider())
    with pytest.raises(HTTPException) as exc:
        svc.approve(case.id, reviewer_user, plate_no="粤A1", violation_type="超速",
                    fine_amount=200, points=6, review_opinion="x")
    assert exc.value.status_code == 409


def test_reject_sets_rejected(db, reviewer_user, pending_case):
    svc = ReviewService(db, FakeNotificationProvider())
    res = svc.reject(pending_case.id, reviewer_user, reject_reason="图片模糊")
    assert res["status"] == "rejected"
    from app.models.intake import Case
    assert db.get(Case, pending_case.id).status == "rejected"


def test_request_recheck_returns_stub(db, reviewer_user, pending_case):
    svc = ReviewService(db, FakeNotificationProvider())
    res = svc.request_recheck(pending_case.id, reviewer_user)
    assert "Plan 2" in res["message"]
