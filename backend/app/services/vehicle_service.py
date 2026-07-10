from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.violation import Vehicle


class VehicleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_vehicle(self, *, plate_no: str, owner_id: int,
                       vehicle_type: str | None, color: str | None) -> Vehicle:
        if self.db.query(Vehicle).filter_by(plate_no=plate_no).first():
            raise HTTPException(status_code=409, detail="车牌号已存在")
        if self.db.get(User, owner_id) is None:
            raise HTTPException(status_code=400, detail="车主不存在")
        v = Vehicle(plate_no=plate_no, owner_id=owner_id, vehicle_type=vehicle_type, color=color)
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

    def list_vehicles(self, *, page: int, page_size: int, plate_no: str | None = None,
                      owner_id: int | None = None) -> dict:
        q = self.db.query(Vehicle)
        if plate_no:
            q = q.filter(Vehicle.plate_no.ilike(f"%{plate_no}%"))
        if owner_id is not None:
            q = q.filter(Vehicle.owner_id == owner_id)
        total = q.count()
        items = q.order_by(Vehicle.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        v = self.db.get(Vehicle, vehicle_id)
        if v is None:
            raise HTTPException(status_code=404, detail="车辆不存在")
        return v

    def update_vehicle(self, vehicle_id: int, *, plate_no: str | None, owner_id: int | None,
                       vehicle_type: str | None, color: str | None) -> Vehicle:
        v = self.get_vehicle(vehicle_id)
        if owner_id is not None and self.db.get(User, owner_id) is None:
            raise HTTPException(status_code=400, detail="车主不存在")
        if plate_no is not None and plate_no != v.plate_no:
            if self.db.query(Vehicle).filter_by(plate_no=plate_no).first():
                raise HTTPException(status_code=409, detail="车牌号已存在")
            v.plate_no = plate_no
        if owner_id is not None:
            v.owner_id = owner_id
        if vehicle_type is not None:
            v.vehicle_type = vehicle_type
        if color is not None:
            v.color = color
        self.db.commit()
        self.db.refresh(v)
        return v

    def unbind_vehicle(self, vehicle_id: int, owner_id: int) -> None:
        vehicle = (
            self.db.query(Vehicle)
            .filter(Vehicle.id == vehicle_id, Vehicle.owner_id == owner_id)
            .first()
        )
        if vehicle is None:
            raise HTTPException(status_code=404, detail="车辆不存在")
        vehicle.owner_id = None
        self.db.commit()
