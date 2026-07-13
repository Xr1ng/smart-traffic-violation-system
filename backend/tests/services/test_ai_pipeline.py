import json
from types import SimpleNamespace

from app.ai.adapters.base import AIReviewResultData, DetectionResult, RuleResult
from app.services import ai_pipeline


def test_ai_pipeline_persists_machine_readable_rule_contract(db, pending_case, tmp_path, monkeypatch):
    image_path = tmp_path / "frame.jpg"
    image_path.write_bytes(b"test-image")
    monkeypatch.setattr(ai_pipeline._settings, "MEDIA_STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr(ai_pipeline, "_detector", lambda: SimpleNamespace(detect=lambda _path: DetectionResult(
        objects=[],
        vehicle_bbox=None,
        plate_bbox=None,
        annotated_image_path=None,
        model_version="test-model",
    )))
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
        lambda: SimpleNamespace(detect=lambda _path: (_ for _ in ()).throw(RuntimeError("boom"))),
    )

    result = ai_pipeline.run_ai_pipeline(pending_case, "/media/frame.jpg")

    assert result["evidence_level"] == "insufficient"
    assert result["candidate_violation_type"] is None
    assert result["conclusion"] == "need_review"
