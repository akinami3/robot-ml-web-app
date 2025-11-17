from enum import Enum

from sqlalchemy import Boolean, Column, Enum as SqlEnum, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class RobotDeviceType(str, Enum):
    SIMULATION = "simulation"
    HARDWARE = "hardware"


class RobotDeviceModel(TimestampMixin, BaseModel):
    __tablename__ = "robot_devices"

    name = Column(String(length=128), nullable=False, unique=True)
    identifier = Column(String(length=128), nullable=False, unique=True)
    kind = Column(SqlEnum(RobotDeviceType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    telemetry_sessions = relationship("TelemetrySessionModel", back_populates="device")
