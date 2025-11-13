"""Dataset session model used for conditional logging."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class DatasetSession(Base, TimestampMixin):
    """Represents a logical data capture session."""

    __tablename__ = "dataset_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    robot_id: Mapped[str] = mapped_column(String(length=64), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    robot_states = relationship("RobotState", back_populates="session")
    sensor_entries = relationship("SensorData", back_populates="session")
    training_runs = relationship("TrainingRun", back_populates="dataset_session")
