# app/api/v1/statistics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.statistics import ByLocationOut, ByTimeOut, ByTypeOut, OverviewOut
from app.services.statistics_service import StatisticsService

router = APIRouter(tags=["statistics"])


def _safe(fn, *args):
    """调用 service；非法 ISO 时间参数（ValueError）转 422 而非 500。"""
    try:
        return fn(*args)
    except ValueError:
        raise HTTPException(status_code=422, detail="start_time/end_time 需 ISO 8601 格式")


@router.get("/statistics/overview", response_model=OverviewOut)
def overview(start_time: str | None = None, end_time: str | None = None,
             db: Session = Depends(get_db),
             _: User = Depends(require_role("reviewer", "admin"))) -> OverviewOut:
    return _safe(StatisticsService(db).overview, start_time, end_time)


@router.get("/statistics/by-location", response_model=ByLocationOut)
def by_location(start_time: str | None = None, end_time: str | None = None,
                limit: int = Query(10, ge=1, le=50),
                db: Session = Depends(get_db),
                _: User = Depends(require_role("reviewer", "admin"))) -> ByLocationOut:
    return _safe(StatisticsService(db).by_location, start_time, end_time, limit)


@router.get("/statistics/by-type", response_model=ByTypeOut)
def by_type(start_time: str | None = None, end_time: str | None = None,
            db: Session = Depends(get_db),
            _: User = Depends(require_role("reviewer", "admin"))) -> ByTypeOut:
    return _safe(StatisticsService(db).by_type, start_time, end_time)


@router.get("/statistics/by-time", response_model=ByTimeOut)
def by_time(start_time: str | None = None, end_time: str | None = None,
            db: Session = Depends(get_db),
            _: User = Depends(require_role("reviewer", "admin"))) -> ByTimeOut:
    return _safe(StatisticsService(db).by_time, start_time, end_time)
