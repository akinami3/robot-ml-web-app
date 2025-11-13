"""Robot state ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class RobotState(Base, TimestampMixin):
    """Latest robot state snapshot."""

    __tablename__ = "robot_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    robot_id: Mapped[str] = mapped_column(String(length=64), nullable=False, index=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_sessions.id"), nullable=True
    )
    battery_level: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    status: Mapped[str] = mapped_column(String(length=32), nullable=False, default="idle")
    last_error: Mapped[str | None] = mapped_column(String(length=256), nullable=True)

    session = relationship("DatasetSession", back_populates="robot_states")
