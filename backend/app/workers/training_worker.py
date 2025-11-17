from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.database.models.training_job import TrainingJobStatus
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from app.repositories.training_repository import TrainingRepository
from app.services.training_service import TrainingService

logger = logging.getLogger(__name__)


@dataclass
class TrainingTask:
    job_id: UUID
    epochs: int


class TrainingWorker:
    def __init__(self, ws_manager: WebSocketConnectionManager) -> None:
        self._queue: asyncio.Queue[TrainingTask] = asyncio.Queue()
        self._ws_manager = ws_manager

    async def enqueue(self, task: TrainingTask) -> None:
        await self._queue.put(task)
        logger.info("Queued training job %s", task.job_id)

    async def run_forever(self) -> None:
        while True:
            task = await self._queue.get()
            await self._run_task(task)
            self._queue.task_done()

    async def _run_task(self, task: TrainingTask) -> None:
        logger.info("Starting training job %s", task.job_id)
        db: Session = SessionLocal()
        repository = TrainingRepository(db)
        service = TrainingService(db, self._ws_manager)
        try:
            repository.set_status(task.job_id, status=TrainingJobStatus.RUNNING)
            for epoch in range(task.epochs):
                loss = 1.0 / (epoch + 1)
                await service.stream_metric(
                    task.job_id,
                    epoch=epoch,
                    step=epoch,
                    metric_name="loss",
                    metric_value=loss,
                )
                await asyncio.sleep(0.1)
            repository.set_status(
                task.job_id,
                status=TrainingJobStatus.COMPLETED,
                model_path=f"models/{task.job_id}.pt",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Training job %s failed: %s", task.job_id, exc)
            repository.set_status(
                task.job_id,
                status=TrainingJobStatus.FAILED,
                error_message=str(exc),
            )
        finally:
            db.close()
