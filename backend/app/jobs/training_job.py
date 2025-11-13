"""Higher level orchestration for ML jobs."""

from __future__ import annotations

import asyncio
import structlog

from app.workers.tasks import train_model_task

logger = structlog.get_logger(__name__)


async def launch_training_job(run_id: str, hyperparameters: dict) -> None:
    logger.info("jobs.launch_training", run_id=run_id)
    await asyncio.to_thread(train_model_task.delay, run_id, hyperparameters)
