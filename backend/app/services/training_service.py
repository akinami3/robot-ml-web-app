from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from app.repositories.training_repository import TrainingRepository
from app.schemas.training import TrainingJob, TrainingJobCreate, TrainingMetric


class TrainingService:
    def __init__(
        self,
        db: Session,
        ws_manager: WebSocketConnectionManager,
    ) -> None:
        self._db = db
        self._repository = TrainingRepository(db)
        self._ws_manager = ws_manager

    def create_job(self, payload: TrainingJobCreate) -> TrainingJob:
        job = self._repository.create_job(
            name=payload.name,
            dataset_session_ids=payload.dataset_session_ids,
            config=payload.config,
        )
        return TrainingJob.from_orm(job)

    async def stream_metric(
        self,
        job_id: UUID,
        *,
        epoch: int,
        step: int,
        metric_name: str,
        metric_value: float,
    ) -> TrainingMetric:
        metric = self._repository.append_metric(
            job_id=job_id,
            epoch=epoch,
            step=step,
            metric_name=metric_name,
            metric_value=metric_value,
        )
        payload = TrainingMetric.from_orm(metric).dict()
        await self._ws_manager.broadcast("training", payload)
        return TrainingMetric.from_orm(metric)

    def list_jobs(self) -> list[TrainingJob]:
        jobs = self._repository.list_jobs()
        return [TrainingJob.from_orm(job) for job in jobs]
