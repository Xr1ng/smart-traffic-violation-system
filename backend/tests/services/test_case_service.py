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
    cam = User(username="cam1", password_hash="h", email="cam1@example.com",
               role_id=seeded_roles["camera"].id)
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


def test_get_case_detail_exposes_red_light_annotation_and_display_text(db, reviewer_user, pending_case):
    pending_case.violation_type = "red_light_violation"
    pending_case.ai_result_json = json.dumps({
        "objects": [
            {"label": "Traffic Light - Red", "confidence": 0.82, "bbox": [1, 2, 3, 4]},
            {"label": "zebra crossing", "confidence": 0.76, "bbox": [5, 6, 7, 8]},
            {
                "label": "suspected_red_light_violation",
                "confidence": 0.71,
                "bbox": [9, 10, 11, 12],
            },
        ],
        "annotated_image_url": "/media/ai_outputs/red-light.jpg",
        "rule_matched": True,
        "candidate_violation_type": "red_light_violation",
        "rule_code": "red_light_zebra_overlap",
        "evidence_level": "partial",
        "evidence_items": [
            "red traffic light detection",
            "zebra crossing detection",
            "vehicle-crossing contact",
        ],
        "missing_evidence": ["plate_localization", "ocr_result"],
        "conclusion": "need_review",
    })
    db.commit()

    detail = CaseService(db).get_case_detail(pending_case.id, user=reviewer_user)

    assert detail["violation_type"] == "疑似闯红灯"
    assert detail["media"]["annotated_url"] == "/media/ai_outputs/red-light.jpg"
    assert detail["detection_result"]["annotated_image_url"] == "/media/ai_outputs/red-light.jpg"
    assert [item["label"] for item in detail["detection_result"]["objects"]] == [
        "红灯",
        "斑马线",
        "疑似闯红灯",
    ]
    assert detail["rule_result"]["evidence_items"] == ["红灯检测", "斑马线检测", "车辆占压斑马线"]
    assert detail["rule_result"]["missing_evidence"] == ["车牌定位", "车牌识别"]


def test_get_case_detail_exposes_primary_target_ids_and_plate_failure(
    db, reviewer_user, pending_case,
):
    pending_case.intake_event.reported_violation_type = "red_light_violation"
    primary_target = {
        "violation_type": "red_light_violation",
        "vehicle": {
            "label": "cars",
            "confidence": 0.91,
            "bbox": [10, 20, 100, 120],
            "model": "vehicle",
            "detection_id": "vehicle-2",
            "display_label": "小汽车2",
        },
        "confidence": 0.86,
        "association_score": 0.8,
        "evidence_bbox": [20, 90, 90, 120],
        "evidence_model": "red_light_rule",
        "is_primary": True,
    }
    pending_case.ai_result_json = json.dumps({
        "objects": [
            {
                "label": "cars",
                "confidence": 0.93,
                "bbox": [0, 0, 40, 50],
                "model": "vehicle",
                "detection_id": "vehicle-1",
                "display_label": "小汽车1",
            },
            primary_target["vehicle"],
        ],
        "reported_violation_type": "red_light_violation",
        "violation_targets": [primary_target],
        "primary_target": primary_target,
        "plate_status": "yolo_not_detected",
        "plate_status_message": "YOLO无法识别车牌/车牌模糊不清",
        "rule_matched": True,
        "candidate_violation_type": "red_light_violation",
        "evidence_level": "partial",
        "evidence_items": ["vehicle-crossing contact"],
        "missing_evidence": ["plate localization"],
        "conclusion": "need_review",
    }, ensure_ascii=False)
    db.commit()

    detail = CaseService(db).get_case_detail(pending_case.id, user=reviewer_user)

    assert detail["reported_violation_type"] == "疑似闯红灯"
    assert detail["plate_status"] == "yolo_not_detected"
    assert detail["plate_status_message"] == "YOLO无法识别车牌/车牌模糊不清"
    objects = detail["detection_result"]["objects"]
    assert [item["display_label"] for item in objects] == ["小汽车1", "小汽车2"]
    assert [item["is_primary"] for item in objects] == [False, True]
    assert detail["detection_result"]["primary_target"]["vehicle"]["detection_id"] == "vehicle-2"


def test_get_case_detail_citizen_other_403(db, pending_case, seeded_roles):
    from app.models.user import User
    other = User(username="citizen2", password_hash="h", email="c2@e.com",
                 role_id=seeded_roles["citizen"].id)
    db.add(other); db.commit()
    svc = CaseService(db)
    with pytest.raises(HTTPException) as exc:
        svc.get_case_detail(pending_case.id, user=other)
    assert exc.value.status_code == 403
