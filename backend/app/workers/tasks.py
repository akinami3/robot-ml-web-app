"""Celery task definitions."""

from __future__ import annotations

import asyncio
import random
import time
import uuid

import structlog

from app.database.session import get_session_factory
from app.repositories.training_metrics import TrainingMetricRepository
from app.repositories.training_runs import TrainingRunRepository
from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.tasks.train_model_task")
def train_model_task(run_id: str, hyperparameters: dict) -> None:
    """Emulate a long running ML training job."""

    async def _train() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            runs = TrainingRunRepository(session)
            metrics = TrainingMetricRepository(session)
            uid = uuid.UUID(run_id)
            await runs.update_status(uid, status="running")
            await session.commit()

            for step in range(1, 6):
                await asyncio.sleep(1)
                loss = random.random()
                await metrics.add_metric(run_id=uid, step=step, name="loss", value=loss)
                await session.commit()

            await runs.update_status(uid, status="completed")
            await session.commit()

    asyncio.run(_train())


@celery_app.task(name="app.workers.tasks.process_batch_telemetry")
def process_batch_telemetry(batch_id: str) -> None:
    logger.info("process_batch_telemetry", batch_id=batch_id)
    time.sleep(1)
