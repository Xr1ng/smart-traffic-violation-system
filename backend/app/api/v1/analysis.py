from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.adapters.base import LLMReportError
from app.ai.providers import get_llm_provider
from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.report import ReportOut, ReportRequest
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


@router.post("/analysis/reports", response_model=ReportOut, status_code=200)
def generate_report(
    body: ReportRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "reviewer")),
) -> ReportOut:
    try:
        provider = get_llm_provider()
        return AnalysisService(db, provider).generate_report(
            body.start_time, body.end_time,
        )
    except (LLMReportError, NotImplementedError) as exc:
        raise HTTPException(
            status_code=503,
            detail="LLM 报告服务暂不可用，请稍后重试",
        ) from exc
