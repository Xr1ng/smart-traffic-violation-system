# tests/services/test_case_service.py
import pytest
from fastapi import HTTPException

from app.services.case_service import CaseService


def test_list_cases_citizen_only_own(db, citizen_user, pending_case):
    svc = CaseService(db)
    res = svc.list_cases(user=citizen_user)
    assert res["total"] == 1
    assert res["items"][0].case_no == "CASE-PEND-1"


def test_list_cases_reviewer_sees_all(db, reviewer_user, pending_case):
    svc = CaseService(db)
    res = svc.list_cases(user=reviewer_user)
    assert res["total"] >= 1


def test_list_cases_camera_forbidden(db, seeded_roles):
    from app.models.user import User
    cam = User(username="cam1", password_hash="h", role_id=seeded_roles["camera"].id)
    db.add(cam); db.commit()
    svc = CaseService(db)
    with pytest.raises(HTTPException) as exc:
        svc.list_cases(user=cam)
    assert exc.value.status_code == 403


def test_get_case_detail_ai_fields_null(db, citizen_user, pending_case):
    svc = CaseService(db)
    d = svc.get_case_detail(pending_case.id, user=citizen_user)
    assert d["case_no"] == "CASE-PEND-1"
    assert d["ai_detection_result"] is None
    assert d["violation_rule_result"] is None
    assert d["ai_review_result"] is None


def test_get_case_detail_reviewer_can_read(db, reviewer_user, pending_case):
    svc = CaseService(db)
    d = svc.get_case_detail(pending_case.id, user=reviewer_user)
    assert d["case_no"] == "CASE-PEND-1"  # reviewer 不抛 403


def test_get_case_detail_citizen_other_403(db, pending_case, seeded_roles):
    from app.models.user import User
    other = User(username="citizen2", password_hash="h", email="c2@e.com",
                 role_id=seeded_roles["citizen"].id)
    db.add(other); db.commit()
    svc = CaseService(db)
    with pytest.raises(HTTPException) as exc:
        svc.get_case_detail(pending_case.id, user=other)
    assert exc.value.status_code == 403
