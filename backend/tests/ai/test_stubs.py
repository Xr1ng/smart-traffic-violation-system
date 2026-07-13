import pytest

from app.ai.adapters.base import DetectionResult, LLMReportError
from app.ai.adapters.stub import (
    StubLLMProvider,
    StubOcrEngine,
    StubRuleEvaluator,
    StubYoloDetector,
)


def test_stub_yolo_detect():
    r = StubYoloDetector().detect("/any.jpg")
    assert r.model_version == "stub-yolov8n"
    assert any(o["label"] == "car" for o in r.objects)
    assert r.vehicle_bbox is not None
    assert r.plate_bbox is not None


def test_stub_ocr_recognize_plate():
    assert StubOcrEngine().recognize_plate("/any.jpg") == "京A12345"


def _det():
    return DetectionResult(
        objects=[], vehicle_bbox=None, plate_bbox=None,
        annotated_image_path=None, model_version="",
    )


def test_stub_rule_speed_matched():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result="京A12345",
        intake_event={"speed": 120},
        rule={"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    )
    assert r.rule_matched is True
    assert r.evidence_level == "complete"
    assert r.candidate_violation_type == "speed"


def test_stub_rule_speed_not_matched():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result=None,
        intake_event={"speed": 50},
        rule={"rule_type": "speed", "speed_limit": 80, "rule_code": "speed"},
    )
    assert r.rule_matched is False


def test_stub_rule_unknown_type():
    r = StubRuleEvaluator().evaluate(
        detection=_det(),
        ocr_result=None,
        intake_event={},
        rule={"rule_type": "no_parking", "rule_code": "np"},
    )
    assert r.rule_matched is False
    assert r.evidence_level == "insufficient"


def test_stub_llm_review():
    r = StubLLMProvider().review({"any": "evidence"})
    assert r.conclusion == "suggest_approve"
    assert r.ai_confidence == 0.88
    assert r.prompt_version == "stub-v1"


def test_stub_llm_report_is_explicitly_unavailable():
    with pytest.raises(LLMReportError, match="未配置"):
        StubLLMProvider().generate_report({"overview": {"total_violations": 0}})
