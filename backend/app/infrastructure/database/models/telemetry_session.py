from enum import Enum

from sqlalchemy import Boolean, Column, Enum as SqlEnum, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class TelemetrySessionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISCARDED = "discarded"


class TelemetrySessionModel(TimestampMixin, BaseModel):
    __tablename__ = "telemetry_sessions"

    device_id = Column(ForeignKey("robot_devices.id"), nullable=False)
    name = Column(String(length=128), nullable=False)
    status = Column(SqlEnum(TelemetrySessionStatus), default=TelemetrySessionStatus.PENDING, nullable=False)
    capture_velocity = Column(Boolean, default=True, nullable=False)
    capture_state = Column(Boolean, default=True, nullable=False)
    capture_images = Column(Boolean, default=False, nullable=False)
    session_metadata = Column(JSON, nullable=True)

    device = relationship("RobotDeviceModel", back_populates="telemetry_sessions")
    records = relationship("TelemetryRecordModel", back_populates="session", cascade="all, delete-orphan")
    media_assets = relationship("MediaAssetModel", back_populates="session", cascade="all, delete-orphan")
