from __future__ import annotations

from ai_service.traffic_ai.schemas import DetectionBundle, ReviewResult, RuleResult


class IllegalStopRuleEvaluator:
    def evaluate(self, detections: DetectionBundle, plate_text: str | None) -> RuleResult:
        illegal = [item for item in detections.illegal_stop if item.label == "illegal"]
        if not illegal:
            return RuleResult(
                candidate_violation_type=None,
                rule_code="illegal_stop_model",
                rule_matched=False,
                evidence_level="insufficient",
                evidence_items=[],
                missing_evidence=["illegal_stop detection"],
                reason="未检测到违停目标",
            )

        evidence = ["illegal_stop detection"]
        missing: list[str] = []
        if detections.vehicle:
            evidence.append("vehicle detection")
        else:
            missing.append("vehicle detection")
        if plate_text:
            evidence.append("plate recognition")
        elif detections.license_plate:
            evidence.append("plate localization")
            missing.append("plate text recognition")
        else:
            missing.append("plate localization")

        return RuleResult(
            candidate_violation_type="illegal_stop",
            rule_code="illegal_stop_model",
            rule_matched=True,
            evidence_level="complete" if not missing else "partial",
            evidence_items=evidence,
            missing_evidence=missing,
            reason="违停模型检测到违章停车目标",
        )


def review_from_rule(rule: RuleResult) -> ReviewResult:
    if rule.rule_matched and rule.evidence_level == "complete":
        return ReviewResult(
            conclusion="suggest_approve",
            confidence=0.85,
            reason="违停证据完整，可提交人工审核",
        )
    if rule.rule_matched:
        return ReviewResult(
            conclusion="need_review",
            confidence=0.65,
            reason="存在违停证据，但部分佐证缺失，需人工复核",
        )
    return ReviewResult(
        conclusion="suggest_reject",
        confidence=0.6,
        reason="未检测到违停证据，建议驳回",
    )
