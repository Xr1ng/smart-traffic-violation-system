# app/services/reward_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.violation import Reward


class RewardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def grant_reward(self, *, citizen_id: int, case_id: int, violation_id: int, violation_type: str) -> Reward:
        reward = Reward(
            citizen_id=citizen_id, case_id=case_id, violation_id=violation_id,
            amount=settings.REWARD_DEFAULT_AMOUNT,
            reason=f"举报{violation_type}成立",
            status="pending",
        )
        self.db.add(reward)
        self.db.flush()
        self.db.commit()
        self.db.refresh(reward)
        return reward

    def list_rewards(self, *, page: int, page_size: int,
                     status: str | None = None) -> dict:
        q = self.db.query(Reward)
        if status:
            q = q.filter(Reward.status == status)
        total = q.count()
        items = q.order_by(Reward.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_reward(self, reward_id: int) -> Reward:
        r = self.db.get(Reward, reward_id)
        if r is None:
            raise HTTPException(status_code=404, detail="奖励记录不存在")
        return r
