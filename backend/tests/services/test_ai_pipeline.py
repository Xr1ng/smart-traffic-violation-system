import json
from types import SimpleNamespace

from app.ai.adapters.base import AIReviewResultData, DetectionResult, RuleResult
from app.services import ai_pipeline


def test_ai_pipeline_persists_yolo_then_ocr_before_llm(
    db, pending_case, tmp_path, monkeypatch,
):
    from app.models.intake import MediaAsset
    from PIL import Image

    Image.new("RGB", (120, 100), "white").save(tmp_path / "frame.jpg")
    (tmp_path / "annotated.jpg").write_bytes(b"annotated")
    pending_case.intake_event.reported_violation_type = "illegal_stop"
    db.commit()
    primary_target = {
        "violation_type": "illegal_stop",
        "vehicle": {
            "label": "cars",
            "confidence": 0.91,
            "bbox": [10, 10, 110, 90],
            "model": "vehicle",
            "detection_id": "vehicle-1",
            "display_label": "car1",
        },
        "confidence": 0.86,
        "association_score": 0.95,
        "evidence_bbox": [10, 10, 110, 90],
        "evidence_model": "illegal_stop",
        "is_primary": True,
    }

    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(detect=lambda _path, _type: DetectionResult(
            objects=[{
                "label": "cars",
                "confidence": 0.91,
                "bbox": [10, 10, 110, 90],
                "model": "vehicle",
            }],
            vehicle_bbox=[10, 10, 110, 90],
            plate_bbox=[40, 60, 80, 78],
            annotated_image_path="/media/annotated.jpg",
            model_version="test-model",
            requested_violation_type="illegal_stop",
            violation_targets=[primary_target],
            primary_target=primary_target,
        )),
    )

    def recognize_plate(_path):
        db.refresh(pending_case)
        yolo_result = json.loads(pending_case.ai_result_json)
        assert pending_case.status == "detecting"
        assert yolo_result["objects"][0]["label"] == "cars"
        assert yolo_result["plate_status"] == "ocr_pending"
        assert db.query(MediaAsset).filter_by(
            intake_event_id=pending_case.intake_event_id,
            asset_type="annotated",
        ).one().url == "/media/annotated.jpg"
        return "\u4eacA12345"

    monkeypatch.setattr(
        ai_pipeline,
        "_ocr",
        lambda: SimpleNamespace(recognize_plate=recognize_plate),
    )
    monkeypatch.setattr(
        ai_pipeline,
        "_evaluator",
        lambda: SimpleNamespace(evaluate=lambda **_kwargs: RuleResult(
            candidate_violation_type="illegal_stop",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="partial",
            evidence_items=["illegal_stop detection"],
            missing_evidence=[],
            reason="suspected illegal stop",
        )),
    )

    def review(_payload):
        db.refresh(pending_case)
        local_result = json.loads(pending_case.ai_result_json)
        assert pending_case.status == "ai_reviewing"
        assert pending_case.plate_no == "\u4eacA12345"
        assert local_result["plate_status"] == "recognized"
        assert local_result["rule_matched"] is True
        assert local_result["conclusion"] is None
        return AIReviewResultData(
            conclusion="need_review",
            ai_confidence=0.7,
            reason="manual review",
            risk_points=[],
            missing_evidence=[],
            prompt_version="test-v1",
        )

    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=review))

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert result["plate_no"] == "\u4eacA12345"
    assert result["conclusion"] == "need_review"
    assert pending_case.status == "pending_human_review"


def test_ai_pipeline_uses_reported_type_and_reports_yolo_plate_failure(
    db, pending_case, tmp_path, monkeypatch,
):
    (tmp_path / "frame.jpg").write_bytes(b"test-image")
    pending_case.intake_event.reported_violation_type = "red_light_violation"
    db.commit()
    captured = {}
    primary_target = {
        "violation_type": "red_light_violation",
        "vehicle": {
            "label": "cars",
            "confidence": 0.91,
            "bbox": [10, 20, 100, 120],
            "model": "vehicle",
            "detection_id": "vehicle-1",
            "display_label": "小汽车1",
        },
        "confidence": 0.86,
        "association_score": 0.8,
        "evidence_bbox": [20, 90, 90, 120],
        "evidence_model": "red_light_rule",
        "is_primary": True,
    }

    def detect(_path, requested_violation_type):
        captured["detector_type"] = requested_violation_type
        return DetectionResult(
            objects=[],
            vehicle_bbox=[10, 20, 100, 120],
            plate_bbox=None,
            annotated_image_path=None,
            model_version="test-model",
            requested_violation_type=requested_violation_type,
            violation_targets=[primary_target],
            primary_target=primary_target,
        )

    def evaluate(**kwargs):
        captured["rule_type"] = kwargs["rule"]["type"]
        return RuleResult(
            candidate_violation_type="red_light_violation",
            rule_code="red_light_zebra_overlap",
            rule_matched=True,
            evidence_level="partial",
            evidence_items=["red traffic light detection", "vehicle-crossing contact"],
            missing_evidence=["plate localization"],
            reason="疑似闯红灯",
        )

    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(ai_pipeline, "_detector", lambda: SimpleNamespace(detect=detect))
    monkeypatch.setattr(ai_pipeline, "_evaluator", lambda: SimpleNamespace(evaluate=evaluate))
    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=lambda _payload: AIReviewResultData(
        conclusion="need_review",
        ai_confidence=0.7,
        reason="需要人工复核",
        risk_points=[],
        missing_evidence=[],
        prompt_version="test-v1",
    )))

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert captured == {
        "detector_type": "red_light_violation",
        "rule_type": "red_light_violation",
    }
    assert result["plate_no"] is None
    assert result["plate_status"] == "yolo_not_detected"
    assert result["plate_status_message"] == "YOLO无法识别车牌/车牌模糊不清"
    assert result["primary_target"]["vehicle"]["detection_id"] == "vehicle-1"


def test_ai_pipeline_persists_machine_readable_rule_contract(db, pending_case, tmp_path, monkeypatch):
    image_path = tmp_path / "frame.jpg"
    image_path.write_bytes(b"test-image")
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(detect=lambda _path, _type: DetectionResult(
            objects=[],
            vehicle_bbox=None,
            plate_bbox=None,
            annotated_image_path=None,
            model_version="test-model",
        )),
    )
    monkeypatch.setattr(ai_pipeline, "_evaluator", lambda: SimpleNamespace(evaluate=lambda **_kwargs: RuleResult(
        candidate_violation_type="illegal_stop",
        rule_code="illegal_stop_model",
        rule_matched=True,
        evidence_level="partial",
        evidence_items=["illegal_stop detection", "vehicle detection", "plate localization"],
        missing_evidence=["plate text recognition"],
        reason="test rule",
    )))
    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=lambda _payload: AIReviewResultData(
        conclusion="need_review",
        ai_confidence=0.65,
        reason="test review",
        risk_points=[],
        missing_evidence=[],
        prompt_version="test-v1",
    )))

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")
    persisted = json.loads(pending_case.ai_result_json)

    assert result["candidate_violation_type"] == "illegal_stop"
    assert result["evidence_items"] == [
        "illegal_stop detection",
        "vehicle detection",
        "plate localization",
    ]
    assert result["missing_evidence"] == ["plate text recognition"]
    assert result["conclusion"] == "need_review"
    assert persisted == result
    assert pending_case.violation_type == "illegal_stop"


def test_ai_pipeline_failure_uses_machine_readable_defaults(db, pending_case, tmp_path, monkeypatch):
    (tmp_path / "frame.jpg").write_bytes(b"test-image")
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(
            detect=lambda _path, _type: (_ for _ in ()).throw(RuntimeError("boom"))
        ),
    )

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert result["evidence_level"] == "insufficient"
    assert result["candidate_violation_type"] is None
    assert result["conclusion"] == "need_review"


def test_ai_pipeline_passes_red_light_evidence_to_llm(db, pending_case, tmp_path, monkeypatch):
    image_path = tmp_path / "frame.jpg"
    image_path.write_bytes(b"test-image")
    annotated_path = "/media/red-light.jpg"
    pending_case.intake_event.reported_violation_type = "red_light_violation"
    db.commit()
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    objects = [
        {
            "label": "suspected_red_light_violation",
            "confidence": 0.86,
            "bbox": [0, 0, 100, 100],
            "model": "red_light_rule",
            "evidence": {"overlap_ratio": 0.5},
        }
    ]
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(detect=lambda _path, _type: DetectionResult(
            objects=objects,
            vehicle_bbox=[0, 0, 100, 100],
            plate_bbox=None,
            annotated_image_path=annotated_path,
            model_version="test-red-light",
        )),
    )
    monkeypatch.setattr(ai_pipeline, "_evaluator", lambda: SimpleNamespace(evaluate=lambda **_kwargs: RuleResult(
        candidate_violation_type="red_light_violation",
        rule_code="red_light_zebra_overlap",
        rule_matched=True,
        evidence_level="partial",
        evidence_items=["red traffic light detection", "vehicle-crossing contact"],
        missing_evidence=["plate localization"],
        reason="疑似闯红灯",
    )))
    captured = {}

    def review(payload):
        captured["payload"] = payload
        return AIReviewResultData(
            conclusion="need_review",
            ai_confidence=0.72,
            reason="需要人工复核",
            risk_points=[],
            missing_evidence=[],
            prompt_version="test-v1",
        )

    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=review))

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert result["candidate_violation_type"] == "red_light_violation"
    assert result["rule_code"] == "red_light_zebra_overlap"
    assert result["annotated_image_url"] == annotated_path
    review_payload = captured["payload"]
    assert review_payload["image_path"] == str(image_path)
    assert review_payload["reported_violation_type"] == "red_light_violation"
    assert review_payload["detection_result"] == {"objects": objects}
    assert review_payload["rule_result"] == {
        "rule_matched": True,
        "evidence_level": "partial",
        "evidence_items": ["red traffic light detection", "vehicle-crossing contact"],
    }
    assert "ocr_result" not in review_payload
    assert "plate_status" not in review_payload
    assert "plate_status_message" not in review_payload


def test_ai_pipeline_registers_generated_annotation_as_case_media(
    db, pending_case, tmp_path, monkeypatch,
):
    from app.models.intake import MediaAsset

    (tmp_path / "frame.jpg").write_bytes(b"original")
    (tmp_path / "annotated.jpg").write_bytes(b"annotated")
    pending_case.intake_event.reported_violation_type = "illegal_stop"
    db.commit()
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(detect=lambda _path, _type: DetectionResult(
            objects=[],
            vehicle_bbox=None,
            plate_bbox=None,
            annotated_image_path="/media/annotated.jpg",
            model_version="test-model",
            requested_violation_type="illegal_stop",
        )),
    )
    monkeypatch.setattr(ai_pipeline, "_evaluator", lambda: SimpleNamespace(evaluate=lambda **_kwargs: RuleResult(
        candidate_violation_type=None,
        rule_code="illegal_stop_model",
        rule_matched=False,
        evidence_level="insufficient",
        evidence_items=[],
        missing_evidence=["illegal_stop detection"],
        reason="未检测到违停",
    )))
    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=lambda _payload: AIReviewResultData(
        conclusion="suggest_reject",
        ai_confidence=0.8,
        reason="未检测到所选违法",
        risk_points=[],
        missing_evidence=[],
        prompt_version="test-v1",
    )))

    ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    asset = db.query(MediaAsset).filter_by(
        intake_event_id=pending_case.intake_event_id,
        asset_type="annotated",
    ).one()
    assert asset.url == "/media/annotated.jpg"
    assert asset.mime_type == "image/jpeg"
    assert asset.size == len(b"annotated")


def test_ai_pipeline_reports_ocr_failure_without_writing_fake_plate(
    db, pending_case, tmp_path, monkeypatch,
):
    from PIL import Image

    Image.new("RGB", (120, 100), "white").save(tmp_path / "frame.jpg")
    pending_case.intake_event.reported_violation_type = "illegal_stop"
    pending_case.plate_no = "BLUCYAL"
    db.commit()
    primary_target = {
        "violation_type": "illegal_stop",
        "vehicle": {
            "label": "cars",
            "confidence": 0.91,
            "bbox": [10, 10, 110, 90],
            "model": "vehicle",
            "detection_id": "vehicle-1",
            "display_label": "小汽车1",
        },
        "confidence": 0.86,
        "association_score": 0.95,
        "evidence_bbox": [10, 10, 110, 90],
        "evidence_model": "illegal_stop",
        "is_primary": True,
    }
    seen_crops = []
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(
        ai_pipeline,
        "_detector",
        lambda: SimpleNamespace(detect=lambda _path, _type: DetectionResult(
            objects=[],
            vehicle_bbox=[10, 10, 110, 90],
            plate_bbox=[40, 60, 80, 78],
            annotated_image_path=None,
            model_version="test-model",
            requested_violation_type="illegal_stop",
            violation_targets=[primary_target],
            primary_target=primary_target,
        )),
    )

    def recognize_plate(path):
        with Image.open(path) as crop:
            seen_crops.append(crop.size)
        return None

    monkeypatch.setattr(ai_pipeline, "_ocr", lambda: SimpleNamespace(recognize_plate=recognize_plate))
    monkeypatch.setattr(ai_pipeline, "_evaluator", lambda: SimpleNamespace(evaluate=lambda **_kwargs: RuleResult(
        candidate_violation_type="illegal_stop",
        rule_code="illegal_stop_model",
        rule_matched=True,
        evidence_level="partial",
        evidence_items=["illegal_stop detection", "offending vehicle association", "plate localization"],
        missing_evidence=["plate text recognition"],
        reason="疑似违停",
    )))
    monkeypatch.setattr(ai_pipeline, "_llm", lambda: SimpleNamespace(review=lambda _payload: AIReviewResultData(
        conclusion="need_review",
        ai_confidence=0.7,
        reason="车牌模糊",
        risk_points=[],
        missing_evidence=[],
        prompt_version="test-v1",
    )))

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert seen_crops == [(40, 18)]
    assert result["plate_no"] is None
    assert result["plate_status"] == "ocr_failed"
    assert result["plate_status_message"] == "OCR无法识别车牌/车牌模糊不清"
    assert pending_case.plate_no is None
