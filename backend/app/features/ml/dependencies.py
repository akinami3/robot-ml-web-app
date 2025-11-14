"""Dependency wiring for the ML feature."""

from __future__ import annotations

from fastapi import Depends, Request

from app.application.interfaces import UnitOfWork
from app.core.base_dependencies import (
    get_celery_app,
    get_unit_of_work,
    get_websocket_hub,
)
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.repositories.training_metrics import TrainingMetricRepository
from app.repositories.training_runs import TrainingRunRepository
from .service import MLPipelineService


__all__ = ["get_ml_pipeline_service"]


async def get_ml_pipeline_service(
    request: Request,
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> MLPipelineService:
    return MLPipelineService(
        unit_of_work=unit_of_work,
        training_run_repo=TrainingRunRepository(unit_of_work.session),
        training_metric_repo=TrainingMetricRepository(unit_of_work.session),
        dataset_repo=DatasetSessionRepository(unit_of_work.session),
        websocket_hub=get_websocket_hub(request),
        celery_app=get_celery_app(request),
    )
