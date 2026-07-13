# tests/services/test_case_service.py
import json

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
    assert d["detection_result"] is None
    assert d["rule_result"] is None
    assert d["ai_review"] is None


def test_get_case_detail_reviewer_can_read(db, reviewer_user, pending_case):
    svc = CaseService(db)
    d = svc.get_case_detail(pending_case.id, user=reviewer_user)
    assert d["case_no"] == "CASE-PEND-1"  # reviewer 不抛 403


def test_get_case_detail_translates_local_ai_contract_for_display(db, reviewer_user, pending_case):
    pending_case.violation_type = "illegal_stop"
    pending_case.ai_result_json = json.dumps({
        "rule_matched": True,
        "candidate_violation_type": "illegal_stop",
        "evidence_level": "partial",
        "evidence_items": ["illegal_stop detection", "plate localization"],
        "missing_evidence": ["plate text recognition"],
        "conclusion": "need_review",
    })
    db.commit()

    detail = CaseService(db).get_case_detail(pending_case.id, user=reviewer_user)

    assert detail["violation_type"] == "违停"
    assert detail["rule_result"]["candidate_violation_type"] == "违停"
    assert detail["rule_result"]["evidence_items"] == ["违停检测", "车牌定位"]
    assert detail["rule_result"]["missing_evidence"] == ["车牌文字识别"]
    assert detail["rule_result"]["evidence_level"] == "部分"
    assert detail["ai_review"]["conclusion"] == "需人工审核"


def test_get_case_detail_citizen_other_403(db, pending_case, seeded_roles):
    from app.models.user import User
    other = User(username="citizen2", password_hash="h", email="c2@e.com",
                 role_id=seeded_roles["citizen"].id)
    db.add(other); db.commit()
    svc = CaseService(db)
    with pytest.raises(HTTPException) as exc:
        svc.get_case_detail(pending_case.id, user=other)
    assert exc.value.status_code == 403
