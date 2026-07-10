# app/services/reward_service.py
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.violation import Reward


class RewardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def grant_reward(self, *, citizen_id: int, case_id: int, violation_id: int, violation_type: str) -> Reward:
        """创建奖励记录（仅 flush，由调用方控制 commit 保证事务原子性）。"""
        reward = Reward(
            citizen_id=citizen_id, case_id=case_id, violation_id=violation_id,
            amount=settings.REWARD_DEFAULT_AMOUNT,
            reason=f"举报{violation_type}成立",
            status="pending",
        )
        self.db.add(reward)
        self.db.flush()
        self.db.refresh(reward)
        return reward

    def mark_paid(self, reward_id: int) -> Reward:
        """标记奖励已发放（原子 UPDATE 防竞态）。"""
        updated = (
            self.db.query(Reward)
            .filter(Reward.id == reward_id, Reward.status != "paid")
            .update({"status": "paid", "paid_at": datetime.now(timezone.utc)},
                    synchronize_session=False)
        )
        if updated == 0:
            reward = self.db.get(Reward, reward_id)
            if reward is None:
                raise HTTPException(status_code=404, detail="奖励不存在")
            raise HTTPException(status_code=409, detail="奖励已发放")
        self.db.commit()
        return self.db.get(Reward, reward_id)

    def list_rewards(self, *, citizen_id: int | None = None, status: str | None = None,
                     page: int = 1, page_size: int = 20) -> dict:
        q = self.db.query(Reward)
        if citizen_id is not None:
            q = q.filter(Reward.citizen_id == citizen_id)
        if status:
            q = q.filter(Reward.status == status)
        total = q.count()
        items = q.order_by(Reward.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_reward(self, reward_id: int) -> Reward:
        reward = self.db.get(Reward, reward_id)
        if reward is None:
            raise HTTPException(status_code=404, detail="奖励不存在")
        return reward
