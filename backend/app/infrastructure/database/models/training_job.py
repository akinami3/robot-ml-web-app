from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, JSON, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class TrainingJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class TrainingJobModel(TimestampMixin, BaseModel):
    __tablename__ = "training_jobs"

    name = Column(String(length=128), nullable=False)
    status = Column(SqlEnum(TrainingJobStatus), default=TrainingJobStatus.PENDING, nullable=False)
    config = Column(JSON, nullable=False)
    dataset_session_ids = Column(JSON, nullable=False)
    model_path = Column(String(length=512), nullable=True)
    error_message = Column(String(length=512), nullable=True)
    owner_id = Column(String(length=64), nullable=True)

    metrics = relationship("TrainingMetricModel", back_populates="job", cascade="all, delete-orphan")
