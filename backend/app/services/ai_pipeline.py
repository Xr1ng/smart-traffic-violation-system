"""AI 管线编排：YOLO → 车牌裁剪 → OCR → 规则 → 审查，结果写回 Case。"""
import json
import logging
import os
from io import BytesIO

from app.ai.adapters.base import DetectionResult
from app.ai.providers import (
    get_llm_provider,
    get_ocr_engine,
    get_rule_evaluator,
    get_yolo_detector,
)
from app.models.intake import Case
from app.core.config import settings as _settings

logger = logging.getLogger(__name__)


def _detector():
    return get_yolo_detector()


def _ocr():
    return get_ocr_engine()


def _evaluator():
    return get_rule_evaluator()


def _llm():
    return get_llm_provider()


def run_ai_pipeline(case: Case, image_relative_url: str) -> dict:
    """对已落盘的原图跑完整 AI 管线，结果写回 case 并 commit 到数据库。
    失败时 case 保持 uploaded 状态，不抛异常。
    """
    image_path = os.path.join(_settings.MEDIA_STORAGE_DIR, os.path.basename(image_relative_url))
    if not os.path.exists(image_path):
        logger.warning("AI pipeline skipped: image not found %s", image_path)
        return {"error": "image_not_found"}

    result = {"model_version": "", "objects": [], "vehicle_bbox": None,
              "plate_bbox": None, "annotated_image_url": None,
              "plate_no": None, "ocr_engine": "无", "ocr_status": "不可用",
              "rule_matched": False, "evidence_level": "insufficient",
              "candidate_violation_type": None,
              "rule_code": "illegal_stop_model",
              "evidence_items": [], "missing_evidence": [], "rule_reason": "",
              "conclusion": "need_review", "ai_confidence": None, "review_reason": ""}

    try:
        # ① YOLO 检测
        detector = _detector()
        detection: DetectionResult = detector.detect(image_path)
        result["model_version"] = detection.model_version
        result["objects"] = detection.objects
        result["vehicle_bbox"] = detection.vehicle_bbox
        result["plate_bbox"] = detection.plate_bbox

        # ② OCR 车牌识别（裁剪车牌区域)
        plate_no = None
        if detection.plate_bbox and len(detection.plate_bbox) == 4:
            try:
                from PIL import Image
                img = Image.open(image_path)
                pb = detection.plate_bbox
                crop = img.crop((pb[0], pb[1], pb[2], pb[3]))
                buf = BytesIO()
                crop.save(buf, format="JPEG")
                buf.seek(0)
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp.write(buf.read())
                    tmp_path = tmp.name
                try:
                    plate_no = _ocr().recognize_plate(tmp_path)
                finally:
                    os.unlink(tmp_path)
            except Exception as e:
                logger.warning("OCR plate crop failed: %s", e)
        result["plate_no"] = plate_no
        result["ocr_engine"] = "PaddleOCR" if plate_no else "不可用"
        result["ocr_status"] = "成功" if plate_no else "失败"

        # ③ 规则判定
        evaluator = _evaluator()
        rule = evaluator.evaluate(
            detection=detection,
            ocr_result=plate_no,
            intake_event={"source_type": "camera"},
            rule={"type": "illegal_stop", "code": "illegal_stop_model"},
        )
        result["rule_matched"] = rule.rule_matched
        result["evidence_level"] = rule.evidence_level
        result["evidence_items"] = rule.evidence_items
        result["missing_evidence"] = rule.missing_evidence
        result["rule_reason"] = rule.reason
        result["candidate_violation_type"] = rule.candidate_violation_type or "illegal_stop"
        result["rule_code"] = rule.rule_code or "illegal_stop_model"

        # ④ LLM 审查
        llm = _llm()
        review = llm.review({
            "image_path": image_path,
            "image_url": image_relative_url,
            "detection_result": {"objects": detection.objects},
            "ocr_result": plate_no,
            "rule_result": {
                "rule_matched": rule.rule_matched,
                "evidence_level": rule.evidence_level,
                "evidence_items": result["evidence_items"],
            },
        })
        result["conclusion"] = review.conclusion
        result["ai_confidence"] = review.ai_confidence
        result["review_reason"] = review.reason
        result["risk_points"] = review.risk_points
        result["missing_evidence"] = review.missing_evidence or result["missing_evidence"]
        result["review_mode"] = "vision_llm" if _settings.LLM_MODE == "vision" else "text_llm"

    except Exception as e:
        logger.exception("AI pipeline failed for case %s: %s", case.case_no, e)
        result["error"] = str(e)
        return result

    # 写回 Case
    from sqlalchemy.orm import Session
    db = Session.object_session(case)
    case.plate_no = plate_no or case.plate_no
    if result.get("candidate_violation_type"):
        case.violation_type = result["candidate_violation_type"]
    case.ai_result_json = json.dumps(result, ensure_ascii=False)
    case.status = "pending_human_review"
    db.commit()
    return result
