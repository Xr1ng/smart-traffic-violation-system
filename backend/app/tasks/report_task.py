"""Celery async task for generating an LLM statistics report."""
from celery import shared_task

from app.ai.providers import get_llm_provider
from app.core.db import SessionLocal
from app.schemas.report import ReportRequest
from app.services.analysis_service import AnalysisService


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_report_task(self, start_time: str, end_time: str) -> dict:
    db = SessionLocal()
    try:
        request = ReportRequest(start_time=start_time, end_time=end_time)
        report = AnalysisService(db, get_llm_provider()).generate_report(
            request.start_time, request.end_time,
        )
        return report.model_dump(mode="json")
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()
