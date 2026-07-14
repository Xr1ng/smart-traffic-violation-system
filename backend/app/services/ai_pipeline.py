"""AI 管线编排：YOLO → 车牌裁剪 → OCR → 规则 → 审查，结果写回 Case。"""
import json
import logging
import os
from io import BytesIO
from pathlib import Path

from app.ai.adapters.base import DetectionResult
from app.ai.providers import (
    get_llm_provider,
    get_ocr_engine,
    get_rule_evaluator,
    get_yolo_detector,
)
from app.models.intake import Case, MediaAsset
from app.core.config import settings as _settings

logger = logging.getLogger(__name__)

PLATE_STATUS_MESSAGES = {
    "ocr_pending": "OCR\u6b63\u5728\u8bc6\u522b\u8f66\u724c",
    "recognized": "车牌识别成功",
    "skipped_no_violation": "未检测到所选疑似违法，未执行车牌识别",
    "yolo_not_detected": "YOLO无法识别车牌/车牌模糊不清",
    "ocr_failed": "OCR无法识别车牌/车牌模糊不清",
}


def _detector():
    return get_yolo_detector()


def _ocr():
    return get_ocr_engine()


def _evaluator():
    return get_rule_evaluator()


def _llm():
    return get_llm_provider()


def _register_annotated_media(case: Case, annotated_url: str | None) -> None:
    if not annotated_url or not annotated_url.startswith("/media/"):
        return
    filename = annotated_url.removeprefix("/media/")
    if not filename or "/" in filename or "\\" in filename:
        logger.warning("Annotated media URL is not a flat media path: %s", annotated_url)
        return

    storage_root = Path(_settings.MEDIA_STORAGE_DIR).resolve()
    annotated_path = (storage_root / filename).resolve()
    if annotated_path.parent != storage_root or not annotated_path.is_file():
        logger.warning("Annotated media file is missing: %s", annotated_path)
        return

    from sqlalchemy.orm import Session

    db = Session.object_session(case)
    asset = db.query(MediaAsset).filter_by(
        intake_event_id=case.intake_event_id,
        asset_type="annotated",
    ).first()
    mime_type = "image/png" if annotated_path.suffix.casefold() == ".png" else "image/jpeg"
    if asset is None:
        asset = MediaAsset(
            intake_event_id=case.intake_event_id,
            asset_type="annotated",
            url=annotated_url,
            mime_type=mime_type,
            size=annotated_path.stat().st_size,
        )
        db.add(asset)
    else:
        asset.url = annotated_url
        asset.mime_type = mime_type
        asset.size = annotated_path.stat().st_size


def _persist_pipeline_snapshot(
    case: Case,
    result: dict,
    *,
    status: str,
    plate_no: str | None,
    register_annotation: bool = False,
) -> None:
    from sqlalchemy.orm import Session

    db = Session.object_session(case)
    if db is None:
        raise RuntimeError("Case is not attached to a database session")
    if register_annotation:
        _register_annotated_media(case, result.get("annotated_image_url"))
    case.plate_no = plate_no
    if result.get("candidate_violation_type"):
        case.violation_type = result["candidate_violation_type"]
    case.ai_result_json = json.dumps(result, ensure_ascii=False)
    case.status = status
    db.commit()


def run_ai_pipeline(case: Case, image_relative_url: str) -> dict:
    """对已落盘的原图跑完整 AI 管线，结果写回 case 并 commit 到数据库。
    失败时 case 保持 uploaded 状态，不抛异常。
    """
    image_path = os.path.join(_settings.MEDIA_STORAGE_DIR, os.path.basename(image_relative_url))
    if not os.path.exists(image_path):
        logger.warning("AI pipeline skipped: image not found %s", image_path)
        return {"error": "image_not_found"}

    reported_violation_type = (
        case.intake_event.reported_violation_type if case.intake_event is not None else None
    )
    result = {"model_version": "", "objects": [], "vehicle_bbox": None,
              "plate_bbox": None, "annotated_image_url": None,
              "reported_violation_type": reported_violation_type,
              "violation_targets": [], "primary_target": None,
              "plate_no": None, "ocr_engine": "none",
              "ocr_status": "skipped_no_violation",
              "plate_status": "skipped_no_violation",
              "plate_status_message": PLATE_STATUS_MESSAGES["skipped_no_violation"],
              "rule_matched": False, "evidence_level": "insufficient",
              "candidate_violation_type": None,
              "rule_code": None,
              "evidence_items": [], "missing_evidence": [], "rule_reason": "",
              "conclusion": None, "ai_confidence": None, "review_reason": "",
              "risk_points": [], "llm_status": "pending", "pipeline_stage": "started"}

    try:
        # ① YOLO 检测
        detector = _detector()
        detection: DetectionResult = detector.detect(image_path, reported_violation_type)
        result["model_version"] = detection.model_version
        result["objects"] = detection.objects
        result["vehicle_bbox"] = detection.vehicle_bbox
        result["plate_bbox"] = detection.plate_bbox
        result["annotated_image_url"] = detection.annotated_image_path
        result["violation_targets"] = detection.violation_targets
        result["primary_target"] = detection.primary_target

        # ② OCR 车牌识别（裁剪车牌区域)
        plate_no = None
        plate_status = "skipped_no_violation"
        ocr_engine = "none"
        has_plate_bbox = bool(detection.plate_bbox and len(detection.plate_bbox) == 4)
        if detection.primary_target is not None and not has_plate_bbox:
            plate_status = "yolo_not_detected"
        elif detection.primary_target is not None:
            plate_status = "ocr_pending"
        result["plate_no"] = plate_no
        result["ocr_engine"] = ocr_engine
        result["ocr_status"] = plate_status
        result["plate_status"] = plate_status
        result["plate_status_message"] = PLATE_STATUS_MESSAGES[plate_status]
        result["pipeline_stage"] = "yolo_complete"
        _persist_pipeline_snapshot(
            case,
            result,
            status="detecting",
            plate_no=None,
            register_annotation=True,
        )

        if plate_status == "ocr_pending":
            plate_status = "ocr_failed"
            try:
                from PIL import Image
                with Image.open(image_path) as img:
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
                ocr_engine = "PaddleOCR"
                if plate_no:
                    plate_status = "recognized"
            except Exception as e:
                logger.warning("OCR plate crop failed: %s", e)
        result["plate_no"] = plate_no
        result["ocr_engine"] = ocr_engine
        result["ocr_status"] = plate_status
        result["plate_status"] = plate_status
        result["plate_status_message"] = PLATE_STATUS_MESSAGES[plate_status]

        # ③ 规则判定
        evaluator = _evaluator()
        rule = evaluator.evaluate(
            detection=detection,
            ocr_result=plate_no,
            intake_event={
                "source_type": case.intake_event.source_type if case.intake_event else None,
                "reported_violation_type": reported_violation_type,
            },
            rule={"type": reported_violation_type or "auto"},
        )
        result["rule_matched"] = rule.rule_matched
        result["evidence_level"] = rule.evidence_level
        result["evidence_items"] = rule.evidence_items
        result["missing_evidence"] = rule.missing_evidence
        result["rule_reason"] = rule.reason
        result["candidate_violation_type"] = rule.candidate_violation_type
        result["rule_code"] = rule.rule_code
        result["pipeline_stage"] = "local_analysis_complete"
        _persist_pipeline_snapshot(
            case,
            result,
            status="ai_reviewing",
            plate_no=plate_no,
        )

        # ④ LLM 审查
        try:
            llm = _llm()
            review = llm.review({
                "image_path": image_path,
                "image_url": image_relative_url,
                "reported_violation_type": reported_violation_type,
                "detection_result": {"objects": detection.objects},
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
            result["llm_status"] = "completed"
        except Exception as llm_error:
            logger.exception("LLM review failed for case %s: %s", case.case_no, llm_error)
            result["conclusion"] = "need_review"
            result["ai_confidence"] = None
            result["review_reason"] = f"LLM unavailable: {llm_error}"
            result["risk_points"] = ["LLM call failed"]
            result["llm_status"] = "failed"
        result["review_mode"] = "vision_llm" if _settings.LLM_MODE == "vision" else "text_llm"
        result["pipeline_stage"] = "complete"

    except Exception as e:
        logger.exception("AI pipeline failed for case %s: %s", case.case_no, e)
        result["error"] = str(e)
        result["conclusion"] = "need_review"
        result["llm_status"] = "skipped"
        return result

    # 写回 Case
    _persist_pipeline_snapshot(
        case,
        result,
        status="pending_human_review",
        plate_no=plate_no,
    )
    return result
