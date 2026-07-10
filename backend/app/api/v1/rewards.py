from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.reward import RewardListResponse, RewardOut
from app.services.reward_service import RewardService

router = APIRouter(prefix="/admin/rewards", tags=["rewards"])


@router.get("", response_model=RewardListResponse)
def list_rewards(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 status: str | None = None, citizen_id: int | None = None,
                 db: Session = Depends(get_db),
                 _: User = Depends(require_role("admin"))) -> RewardListResponse:
    res = RewardService(db).list_rewards(page=page, page_size=page_size,
                                         status=status, citizen_id=citizen_id)
    return RewardListResponse(
        items=[RewardOut.model_validate(r) for r in res["items"]],
        total=res["total"], page=res["page"], page_size=res["page_size"])


@router.get("/{reward_id}", response_model=RewardOut)
def get_reward(reward_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> RewardOut:
    return RewardOut.model_validate(RewardService(db).get_reward(reward_id))


@router.post("/{reward_id}/pay", response_model=RewardOut)
def pay_reward(reward_id: int, db: Session = Depends(get_db),
               _: User = Depends(require_role("admin"))) -> RewardOut:
    return RewardOut.model_validate(RewardService(db).mark_paid(reward_id))
