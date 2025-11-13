"""Sensor data ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class SensorData(Base, TimestampMixin):
    """Raw telemetry captured from MQTT topics."""

    __tablename__ = "sensor_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_sessions.id"), nullable=False
    )
    sensor_type: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    session = relationship("DatasetSession", back_populates="sensor_entries")
