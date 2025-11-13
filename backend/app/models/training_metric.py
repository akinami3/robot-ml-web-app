"""Training metrics recorded over time."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class TrainingMetric(Base, TimestampMixin):
    """Captures metric values for a training run."""

    __tablename__ = "training_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_runs.id"), nullable=False
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    run = relationship("TrainingRun", back_populates="metrics")
