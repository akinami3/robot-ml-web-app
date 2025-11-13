"""ML pipeline endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_ml_pipeline_service
from app.schemas.ml import TrainingConfig, TrainingLaunchResponse, TrainingMetricSnapshot
from app.services.ml_pipeline import MLPipelineService, TrainingConfigPayload

router = APIRouter()


@router.post("/train", response_model=TrainingLaunchResponse)
async def launch_training(
    config: TrainingConfig,
    service: MLPipelineService = Depends(get_ml_pipeline_service),
) -> TrainingLaunchResponse:
    run_id = await service.launch_training(
        TrainingConfigPayload(
            model_name=config.model_name,
            robot_id=config.robot_id,
            hyperparameters=config.hyperparameters,
            dataset_session_id=config.dataset_session_id,
        )
    )
    return TrainingLaunchResponse(run_id=run_id)


@router.get("/runs/{run_id}", response_model=list[TrainingMetricSnapshot])
async def get_run_metrics(
    run_id: uuid.UUID,
    service: MLPipelineService = Depends(get_ml_pipeline_service),
) -> list[TrainingMetricSnapshot]:
    metrics = await service.get_run_metrics(run_id)
    if not metrics:
        run = await service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="training run not found")
    return [TrainingMetricSnapshot(**metric) for metric in metrics]
