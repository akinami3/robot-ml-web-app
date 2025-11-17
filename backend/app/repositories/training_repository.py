from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.database.models.training_job import TrainingJobModel, TrainingJobStatus
from app.infrastructure.database.models.training_metric import TrainingMetricModel


class TrainingRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_job(self, *, name: str, dataset_session_ids: list[UUID], config: dict) -> TrainingJobModel:
        job = TrainingJobModel(
            name=name,
            dataset_session_ids=[str(item) for item in dataset_session_ids],
            config=config,
            status=TrainingJobStatus.PENDING,
        )
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job

    def set_status(
        self,
        job_id: UUID,
        *,
        status: TrainingJobStatus,
        model_path: str | None = None,
        error_message: str | None = None,
    ) -> TrainingJobModel:
        job = self._db.query(TrainingJobModel).filter(TrainingJobModel.id == job_id).one()
        job.status = status
        job.model_path = model_path
        job.error_message = error_message
        self._db.commit()
        self._db.refresh(job)
        return job

    def append_metric(
        self,
        job_id: UUID,
        *,
        epoch: int,
        step: int,
        metric_name: str,
        metric_value: float,
    ) -> TrainingMetricModel:
        metric = TrainingMetricModel(
            job_id=job_id,
            epoch=epoch,
            step=step,
            metric_name=metric_name,
            metric_value=metric_value,
        )
        self._db.add(metric)
        self._db.commit()
        self._db.refresh(metric)
        return metric

    def list_jobs(self) -> Sequence[TrainingJobModel]:
        return self._db.query(TrainingJobModel).order_by(TrainingJobModel.created_at.desc()).all()
