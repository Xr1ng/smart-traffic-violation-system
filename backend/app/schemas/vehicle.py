from datetime import datetime

from pydantic import BaseModel


class VehicleOut(BaseModel):
    id: int
    plate_no: str
    owner_id: int | None
    vehicle_type: str | None
    color: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class VehicleCreateIn(BaseModel):
    plate_no: str
    owner_id: int
    vehicle_type: str | None = None
    color: str | None = None


class VehicleBindIn(BaseModel):
    plate_no: str
    vehicle_type: str | None = None
    color: str | None = None


class VehicleUpdateIn(BaseModel):
    plate_no: str | None = None
    owner_id: int | None = None
    vehicle_type: str | None = None
    color: str | None = None


class VehicleListResponse(BaseModel):
    items: list[VehicleOut]
    total: int
    page: int
    page_size: int
