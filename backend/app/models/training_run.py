"""Training run metadata."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class TrainingRun(Base, TimestampMixin):
    """Represents an ML training job."""

    __tablename__ = "training_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_sessions.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(length=32), default="queued")
    model_name: Mapped[str] = mapped_column(String(length=128), nullable=False)
    params: Mapped[dict | None] = mapped_column(nullable=True)

    dataset_session = relationship("DatasetSession", back_populates="training_runs")
    metrics = relationship("TrainingMetric", back_populates="run", cascade="all,delete")
