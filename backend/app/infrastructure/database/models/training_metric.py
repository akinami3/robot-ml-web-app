from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class TrainingMetricModel(TimestampMixin, BaseModel):
    __tablename__ = "training_metrics"

    job_id = Column(ForeignKey("training_jobs.id"), nullable=False, index=True)
    epoch = Column(Integer, nullable=False)
    step = Column(Integer, nullable=False)
    metric_name = Column(String(length=64), nullable=False)
    metric_value = Column(Float, nullable=False)

    job = relationship("TrainingJobModel", back_populates="metrics")
