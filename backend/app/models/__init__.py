"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


Timestamp = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]


class TimestampMixin:
    """Mixin that adds created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# Re-export frequently used models for convenience.
from .dataset_session import DatasetSession  # noqa: E402
from .rag_document import RAGDocument  # noqa: E402
from .robot_state import RobotState  # noqa: E402
from .sensor_data import SensorData  # noqa: E402
from .training_metric import TrainingMetric  # noqa: E402
from .training_run import TrainingRun  # noqa: E402

__all__ = [
    "Base",
    "TimestampMixin",
    "DatasetSession",
    "RobotState",
    "SensorData",
    "TrainingRun",
    "TrainingMetric",
    "RAGDocument",
]
