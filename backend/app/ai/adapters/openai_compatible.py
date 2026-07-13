"""OpenAI-compatible LLM adapter for traffic violation review."""
from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from app.ai.adapters.base import (
    AIReviewResultData,
    LLMProvider,
    LLMReportError,
    ReportNarrativeData,
)

PostJson = Callable[[str, dict[str, str], dict, float], dict]


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        text_model: str,
        vision_model: str,
        mode: str = "text",
        timeout_seconds: float = 30,
        post_json: PostJson | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.text_model = text_model
        self.vision_model = vision_model
        self.mode = mode
        self.timeout_seconds = timeout_seconds
        self._post_json = post_json or _post_json

    def review(self, evidence_payload: dict) -> AIReviewResultData:
        try:
            payload = self._build_chat_payload(evidence_payload)
            data = self._post_json(
                f"{self.base_url}/chat/completions",
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                payload,
                self.timeout_seconds,
            )
            return _parse_review_response(data)
        except Exception as exc:
            return AIReviewResultData(
                conclusion="need_review",
                ai_confidence=None,
                reason=f"LLM unavailable, please rely on YOLO/rule result for human review: {exc}",
                risk_points=["LLM call failed"],
                missing_evidence=[],
                prompt_version="openai-compatible-fallback-v1",
            )

    def generate_report(self, statistics_payload: dict) -> ReportNarrativeData:
        try:
            data = self._post_json(
                f"{self.base_url}/chat/completions",
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                {
                    "model": self.text_model,
                    "temperature": 0.2,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是交通管理数据分析助手。只能依据提供的聚合统计数据生成中文报告，"
                                "不得编造增长率、地点、治理成效或未提供的事实。数据不足时必须明确说明。"
                                "只输出 JSON，且必须包含 summary、trend_analysis、hotspot_analysis、"
                                "risk_alerts、recommendations 五个字段；后两个字段必须为字符串数组。"
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                "请生成交通违章综合分析报告的结构化正文。聚合统计 JSON：\n"
                                f"{json.dumps(statistics_payload, ensure_ascii=False, default=str)}"
                            ),
                        },
                    ],
                },
                self.timeout_seconds,
            )
            content = data["choices"][0]["message"]["content"]
            return ReportNarrativeData.model_validate(_loads_json_object(content))
        except Exception as exc:
            raise LLMReportError("LLM 报告生成失败") from exc

    def _build_chat_payload(self, evidence_payload: dict) -> dict:
        image_path = _find_image_path(evidence_payload) if self.mode == "vision" else None
        model = self.vision_model if image_path else self.text_model
        return {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是交通违法审核辅助系统。只根据输入的 YOLO 检测结果、规则结果和图片信息给出"
                        "人工复核建议，不要声称已经完成执法处罚。必须输出 JSON。"
                    ),
                },
                {"role": "user", "content": _build_user_content(evidence_payload, image_path)},
            ],
        }


def _build_user_content(evidence_payload: dict, image_path: Path | None):
    text = (
        "请根据以下证据生成交通违法初审建议。输出 JSON 字段："
        "conclusion(suggest_approve/need_review/suggest_reject), "
        "ai_confidence(0-1 或 null), reason, risk_points 数组, missing_evidence 数组。\n\n"
        f"证据 JSON：{json.dumps(evidence_payload, ensure_ascii=False, default=str)}"
    )
    if image_path is None:
        return text
    return [
        {"type": "text", "text": text},
        {"type": "image_url", "image_url": {"url": _image_to_data_url(image_path)}},
    ]


def _find_image_path(evidence_payload: dict) -> Path | None:
    candidates = [
        evidence_payload.get("image_path"),
        evidence_payload.get("annotated_image_path"),
        evidence_payload.get("annotated_image_url"),
        evidence_payload.get("original_image_path"),
        evidence_payload.get("image_url"),
    ]
    detection = evidence_payload.get("detection")
    if isinstance(detection, dict):
        candidates.extend([detection.get("annotated_image_path"), detection.get("annotated_image_url")])

    for value in candidates:
        if not value:
            continue
        path = Path(str(value))
        # 如果是相对 URL（如 /media/xxx.jpg），补上 MEDIA_STORAGE_DIR 前缀
        if not path.exists() and str(value).startswith("/media/"):
            from app.core.config import settings
            alt = Path(settings.MEDIA_STORAGE_DIR) / path.name
            if alt.exists() and alt.is_file():
                return alt
        if path.exists() and path.is_file():
            return path
    return None


def _image_to_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _parse_review_response(data: dict) -> AIReviewResultData:
    content = data["choices"][0]["message"]["content"]
    parsed = _loads_json_object(content)
    return AIReviewResultData(
        conclusion=str(parsed.get("conclusion") or "need_review"),
        ai_confidence=parsed.get("ai_confidence"),
        reason=str(parsed.get("reason") or content),
        risk_points=list(parsed.get("risk_points") or []),
        missing_evidence=list(parsed.get("missing_evidence") or []),
        prompt_version="openai-compatible-review-v1",
    )


def _loads_json_object(content: str) -> dict:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        return {"conclusion": "need_review", "reason": content}


def _post_json(url: str, headers: dict[str, str], payload: dict, timeout: float) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail}") from exc
