from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class MediaAssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class MediaAssetModel(TimestampMixin, BaseModel):
    __tablename__ = "media_assets"

    session_id = Column(ForeignKey("telemetry_sessions.id"), nullable=False, index=True)
    record_id = Column(ForeignKey("telemetry_records.id"), nullable=True, index=True)
    asset_type = Column(SqlEnum(MediaAssetType), nullable=False)
    file_path = Column(String(length=512), nullable=False, unique=True)
    checksum = Column(String(length=128), nullable=True)
    mime_type = Column(String(length=64), nullable=True)

    session = relationship("TelemetrySessionModel", back_populates="media_assets")
    record = relationship("TelemetryRecordModel", back_populates="media_assets")
