from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class TelemetryRecordModel(TimestampMixin, BaseModel):
    __tablename__ = "telemetry_records"

    session_id = Column(ForeignKey("telemetry_sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    linear_velocity_x = Column(Float, nullable=True)
    linear_velocity_y = Column(Float, nullable=True)
    angular_velocity_z = Column(Float, nullable=True)
    state = Column(JSON, nullable=True)
    notes = Column(String(length=256), nullable=True)

    session = relationship("TelemetrySessionModel", back_populates="records")
    media_assets = relationship("MediaAssetModel", back_populates="record")
