"""Machine learning pipeline use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from celery import Celery

from app.application.interfaces import UnitOfWork, WebSocketBroadcaster
from app.infrastructure.realtime import ML_CHANNEL
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.repositories.training_metrics import TrainingMetricRepository
from app.repositories.training_runs import TrainingRunRepository


@dataclass(slots=True)
class TrainingConfigPayload:
    model_name: str
    robot_id: str
    hyperparameters: dict[str, Any]
    dataset_session_id: uuid.UUID | None = None


class MLPipelineUseCase:
    """Launches and monitors ML training jobs."""

    def __init__(
        self,
        *,
        unit_of_work: UnitOfWork,
        training_run_repo: TrainingRunRepository,
        training_metric_repo: TrainingMetricRepository,
        dataset_repo: DatasetSessionRepository,
        websocket_hub: WebSocketBroadcaster,
        celery_app: Celery,
    ) -> None:
        self._uow = unit_of_work
        self._training_runs = training_run_repo
        self._training_metrics = training_metric_repo
        self._dataset_repo = dataset_repo
        self._ws_hub = websocket_hub
        self._celery = celery_app

    async def launch_training(self, payload: TrainingConfigPayload) -> uuid.UUID:
        dataset_session_id = payload.dataset_session_id
        if dataset_session_id is None:
            active = await self._dataset_repo.get_active_by_robot(payload.robot_id)
            dataset_session_id = active.id if active else None

        run = await self._training_runs.create_run(
            model_name=payload.model_name,
            dataset_session_id=dataset_session_id,
            params=payload.hyperparameters,
        )
        await self._uow.commit()

        self._celery.send_task(
            "app.workers.tasks.train_model_task",
            args=[str(run.id), payload.hyperparameters],
        )

        await self._ws_hub.broadcast(
            channel=ML_CHANNEL,
            message={"event": "training_queued", "run_id": str(run.id)},
        )
        return run.id

    async def get_run_metrics(self, run_id: uuid.UUID) -> list[dict[str, Any]]:
        metrics = await self._training_metrics.list_for_run(run_id)
        return [
            {
                "step": metric.step,
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.created_at.isoformat(),
            }
            for metric in metrics
        ]

    async def get_run(self, run_id: uuid.UUID):
        return await self._training_runs.get(run_id)


__all__ = ["TrainingConfigPayload", "MLPipelineUseCase"]
