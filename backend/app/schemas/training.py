from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.infrastructure.database.models.training_job import TrainingJobStatus


class TrainingJobCreate(BaseModel):
    name: str
    dataset_session_ids: list[UUID]
    config: dict


class TrainingJob(BaseModel):
    id: UUID
    name: str
    status: TrainingJobStatus
    dataset_session_ids: list[str]
    config: dict
    model_path: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TrainingMetric(BaseModel):
    job_id: UUID
    epoch: int
    step: int
    metric_name: str
    metric_value: float
    created_at: datetime

    class Config:
        orm_mode = True


class TrainingJobStatusUpdate(BaseModel):
    status: TrainingJobStatus
    model_path: str | None = None
    error_message: str | None = None
