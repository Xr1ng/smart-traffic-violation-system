# app/models/intake.py
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IntakeEvent(Base):
    __tablename__ = "intake_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(16))  # citizen/camera/admin
    source_id: Mapped[int | None] = mapped_column()  # 举报人/管理员/摄像头 id
    location_text: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(512))
    longitude: Mapped[float | None] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    speed: Mapped[float | None] = mapped_column(Float)
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    cases: Mapped[list["Case"]] = relationship(back_populates="intake_event")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="intake_event")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    intake_event_id: Mapped[int] = mapped_column(ForeignKey("intake_events.id"))
    intake_event: Mapped["IntakeEvent"] = relationship(back_populates="media_assets")
    asset_type: Mapped[str] = mapped_column(String(16))  # original/annotated/cropped_plate
    url: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    intake_event_id: Mapped[int] = mapped_column(ForeignKey("intake_events.id"))
    intake_event: Mapped["IntakeEvent"] = relationship(back_populates="cases")
    status: Mapped[str] = mapped_column(String(24), default="uploaded")
    plate_no: Mapped[str | None] = mapped_column(String(16))
    violation_type: Mapped[str | None] = mapped_column(String(32))
    reviewer_id: Mapped[int | None] = mapped_column()
    review_opinion: Mapped[str | None] = mapped_column(String(512))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CameraDevice(Base):
    __tablename__ = "camera_devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    location_text: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="enabled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class CameraApiKey(Base):
    __tablename__ = "camera_api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_device_id: Mapped[int] = mapped_column(ForeignKey("camera_devices.id"))
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
