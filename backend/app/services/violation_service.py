# app/services/violation_service.py
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.intake import Case
from app.models.user import User
from app.models.violation import Vehicle, Violation


def get_owner_email(db: Session, violation: Violation) -> str | None:
    if not violation.owner_id:
        return None
    owner = db.get(User, violation.owner_id)
    return owner.email if owner else None


class ViolationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_violation(self, case: Case, *, plate_no: str, violation_type: str,
                         fine_amount: int, points: int) -> Violation:
        vehicle = self.db.query(Vehicle).filter(Vehicle.plate_no == plate_no).first()
        owner_id = vehicle.owner_id if vehicle else None
        ev = case.intake_event
        v = Violation(
            violation_no="placeholder",
            case_id=case.id,
            vehicle_id=vehicle.id if vehicle else None,
            owner_id=owner_id,
            plate_no=plate_no,
            violation_type=violation_type,
            fine_amount=fine_amount,
            points=points,
            occurred_at=ev.captured_at if ev else None,
            location_text=ev.location_text if ev else None,
            status="pending",
        )
        self.db.add(v)
        self.db.flush()
        v.violation_no = f"VIO{datetime.now(timezone.utc):%Y%m%d}{v.id:06d}"
        self.db.flush()
        return v

    def list_violations(self, *, plate_no: str | None = None, violation_type: str | None = None,
                        status: str | None = None, start_time=None, end_time=None,
                        location_text: str | None = None,
                        page: int = 1, page_size: int = 20) -> dict:
        q = self.db.query(Violation)
        if plate_no:
            q = q.filter(Violation.plate_no == plate_no)
        if violation_type:
            q = q.filter(Violation.violation_type == violation_type)
        if status:
            q = q.filter(Violation.status == status)
        if start_time:
            q = q.filter(Violation.occurred_at >= start_time)
        if end_time:
            q = q.filter(Violation.occurred_at <= end_time)
        if location_text:
            q = q.filter(Violation.location_text.ilike(f"%{location_text}%"))
        total = q.count()
        items = q.order_by(Violation.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_violation(self, vid: int) -> Violation | None:
        return self.db.get(Violation, vid)

    def list_by_owner(self, owner_id: int, *, page: int = 1, page_size: int = 20) -> dict:
        q = self.db.query(Violation).filter(Violation.owner_id == owner_id)
        total = q.count()
        items = q.order_by(Violation.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
