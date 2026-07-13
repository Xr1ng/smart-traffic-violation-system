"""Stub AI 实现 — 返回写实固定数据，供管线联调。

real 实现由唐高鹏交付后接入 providers.py 的工厂分支，不改路由。
"""
from app.ai.adapters.base import (
    AIReviewResultData,
    DetectionResult,
    LLMProvider,
    LLMReportError,
    OcrEngine,
    ReportNarrativeData,
    RuleEvaluator,
    RuleResult,
    YoloDetector,
)


class StubYoloDetector(YoloDetector):
    def detect(self, image_path: str) -> DetectionResult:
        return DetectionResult(
            objects=[{"label": "car", "confidence": 0.92, "bbox": [100, 200, 300, 350]}],
            vehicle_bbox=[100, 200, 300, 350],
            plate_bbox=[120, 230, 200, 270],
            annotated_image_path=None,  # stub 不产标注图；real 实现返回持久化 URL
            model_version="stub-yolov8n",
        )


class StubOcrEngine(OcrEngine):
    def recognize_plate(self, plate_crop_path: str) -> str | None:
        return "京A12345"


class StubRuleEvaluator(RuleEvaluator):
    def evaluate(self, detection, ocr_result, intake_event, rule) -> RuleResult:
        rule_type = rule.get("rule_type")
        if rule_type == "speed":
            speed = intake_event.get("speed")
            limit = rule.get("speed_limit")
            matched = speed is not None and limit is not None and speed > limit
            return RuleResult(
                candidate_violation_type="speed" if matched else None,
                rule_code=rule.get("rule_code", "speed"),
                rule_matched=matched,
                evidence_level="complete" if matched else "insufficient",
                evidence_items=[f"车速{speed}，限速{limit}"] if matched else [],
                missing_evidence=[] if matched else ["车速或限速缺失"],
                reason="超速判定" if matched else "速度数据不足",
            )
        if rule_type == "special_lane":
            return RuleResult(
                candidate_violation_type="special_lane",
                rule_code=rule.get("rule_code", "special_lane"),
                rule_matched=True,
                evidence_level="complete",
                evidence_items=["检测到车辆", "车辆位于专用车道ROI内"],
                missing_evidence=[],
                reason="占用专用车道（stub 简化：默认匹配）",
            )
        return RuleResult(
            candidate_violation_type=None,
            rule_code=rule.get("rule_code"),
            rule_matched=False,
            evidence_level="insufficient",
            evidence_items=[],
            missing_evidence=[f"未知 rule_type: {rule_type}"],
            reason="未知规则",
        )


class StubLLMProvider(LLMProvider):
    def review(self, evidence_payload: dict) -> AIReviewResultData:
        return AIReviewResultData(
            conclusion="suggest_approve",
            ai_confidence=0.88,
            reason="证据链完整，建议通过",
            risk_points=[],
            missing_evidence=[],
            prompt_version="stub-v1",
        )

    def generate_report(self, statistics_payload: dict) -> ReportNarrativeData:
        raise LLMReportError("LLM 未配置，无法生成分析报告")
