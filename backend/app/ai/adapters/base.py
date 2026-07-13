"""AI 组件抽象接口 — 可插拔，每组件一套实现，后期可换。

real 实现由唐高鹏交付（YOLOv8/OCR/规则引擎/LLM），张浩-10 提供 stub + 路由。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class DetectionResult:
    objects: list[dict]  # [{label, confidence, bbox}, ...]
    vehicle_bbox: list[int] | None  # [x1, y1, x2, y2]
    plate_bbox: list[int] | None
    annotated_image_path: str | None
    model_version: str


@dataclass
class RuleResult:
    candidate_violation_type: str | None
    rule_code: str | None
    rule_matched: bool
    evidence_level: str  # complete / partial / insufficient
    evidence_items: list[str]
    missing_evidence: list[str]
    reason: str


@dataclass
class AIReviewResultData:
    conclusion: str  # suggest_approve / need_review / suggest_reject
    ai_confidence: float | None
    reason: str
    risk_points: list[str]
    missing_evidence: list[str]
    prompt_version: str


class ReportNarrativeData(BaseModel):
    summary: str
    trend_analysis: str
    hotspot_analysis: str
    risk_alerts: list[str]
    recommendations: list[str]


class LLMReportError(RuntimeError):
    """The configured LLM could not produce a valid analysis report."""


class YoloDetector(ABC):
    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult: ...


class OcrEngine(ABC):
    @abstractmethod
    def recognize_plate(self, plate_crop_path: str) -> str | None: ...


class RuleEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        detection: DetectionResult,
        ocr_result: str | None,
        intake_event: dict,
        rule: dict,
    ) -> RuleResult: ...


class LLMProvider(ABC):
    @abstractmethod
    def review(self, evidence_payload: dict) -> AIReviewResultData: ...

    @abstractmethod
    def generate_report(self, statistics_payload: dict) -> ReportNarrativeData: ...
