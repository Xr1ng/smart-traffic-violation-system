from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.adapters.base import LLMReportError
from app.ai.providers import get_llm_provider
from app.core.config import settings
from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.report import (
    ReportHistoryPage,
    ReportRequest,
    SavedReportOut,
)
from app.services.analysis_service import AnalysisService
from app.services.report_storage import ReportStorageError, ReportStorageService

router = APIRouter(tags=["analysis"])


@router.post("/analysis/reports", response_model=SavedReportOut, status_code=200)
def generate_report(
    body: ReportRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "reviewer")),
) -> SavedReportOut:
    try:
        provider = get_llm_provider()
        report = AnalysisService(db, provider).generate_report(
            body.start_time, body.end_time,
        )
        return ReportStorageService(settings.REPORT_STORAGE_DIR).save(report)
    except (LLMReportError, NotImplementedError) as exc:
        raise HTTPException(
            status_code=503,
            detail="LLM 报告服务暂不可用，请稍后重试",
        ) from exc
    except ReportStorageError as exc:
        raise HTTPException(
            status_code=500,
            detail="报告已生成但保存失败，请稍后重试",
        ) from exc


@router.get("/analysis/reports", response_model=ReportHistoryPage)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    _: User = Depends(require_role("admin", "reviewer")),
) -> ReportHistoryPage:
    start_time, end_time = _validate_history_window(start_time, end_time)
    return ReportStorageService(settings.REPORT_STORAGE_DIR).list(
        page=page,
        page_size=page_size,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/analysis/reports/{report_id}", response_model=SavedReportOut)
def get_report(
    report_id: str,
    _: User = Depends(require_role("admin", "reviewer")),
) -> SavedReportOut:
    try:
        return ReportStorageService(settings.REPORT_STORAGE_DIR).get(report_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="历史报告不存在") from exc
    except ReportStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _validate_history_window(
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if (start_time is None) != (end_time is None):
        raise HTTPException(status_code=422, detail="start_time 和 end_time 必须同时提供")
    if start_time is None or end_time is None:
        return None, None
    start_time = _as_utc(start_time)
    end_time = _as_utc(end_time)
    if start_time > end_time:
        raise HTTPException(status_code=422, detail="start_time 不能晚于 end_time")
    return start_time, end_time


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
