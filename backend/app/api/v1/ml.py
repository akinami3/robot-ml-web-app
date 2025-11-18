"""
Machine Learning API endpoints
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_ws_manager
from app.core.websocket import ConnectionManager
from app.dependencies import get_db
from app.repositories.ml_model import MLModelRepository
from app.schemas.ml import (
    EvaluationResult,
    MLModelCreate,
    MLModelResponse,
    TrainingMetricsResponse,
    TrainingStartRequest,
    TrainingStopRequest,
)
from app.services.ml.training_service import get_training_service

router = APIRouter()


# Model Management Endpoints
@router.post("/models", response_model=MLModelResponse)
async def create_model(model: MLModelCreate, db: AsyncSession = Depends(get_db)):
    """Create new ML model"""
    model_repo = MLModelRepository(db)
    ml_model = await model_repo.create(model.dict())
    await db.commit()
    
    return MLModelResponse(
        id=ml_model.id,
        name=ml_model.name,
        model_type=ml_model.model_type,
        architecture=ml_model.architecture,
        status=ml_model.status,
        created_at=ml_model.created_at,
        last_trained_at=ml_model.last_trained_at
    )


@router.get("/models", response_model=List[MLModelResponse])
async def list_models(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """List all ML models"""
    model_repo = MLModelRepository(db)
    models = await model_repo.get_multi(skip=skip, limit=limit)
    
    return [
        MLModelResponse(
            id=m.id,
            name=m.name,
            model_type=m.model_type,
            architecture=m.architecture,
            status=m.status,
            created_at=m.created_at,
            last_trained_at=m.last_trained_at
        )
        for m in models
    ]


@router.get("/models/{model_id}", response_model=MLModelResponse)
async def get_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get ML model details"""
    model_repo = MLModelRepository(db)
    ml_model = await model_repo.get(model_id)
    
    if not ml_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return MLModelResponse(
        id=ml_model.id,
        name=ml_model.name,
        model_type=ml_model.model_type,
        architecture=ml_model.architecture,
        status=ml_model.status,
        created_at=ml_model.created_at,
        last_trained_at=ml_model.last_trained_at
    )


@router.delete("/models/{model_id}")
async def delete_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete ML model"""
    model_repo = MLModelRepository(db)
    success = await model_repo.delete(model_id)
    await db.commit()
    
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"status": "deleted", "model_id": str(model_id)}


# Training Endpoints
@router.post("/training/start")
async def start_training(
    request: TrainingStartRequest,
    db: AsyncSession = Depends(get_db),
    ws_manager: ConnectionManager = Depends(get_ws_manager),
):
    """Start model training"""
    training_service = get_training_service(ws_manager)
    return await training_service.start_training(db, request.model_id, request.config)


@router.post("/training/stop")
async def stop_training(
    request: TrainingStopRequest,
    db: AsyncSession = Depends(get_db),
    ws_manager: ConnectionManager = Depends(get_ws_manager),
):
    """Stop model training"""
    training_service = get_training_service(ws_manager)
    return await training_service.stop_training(db, request.model_id)
    """Stop model training"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/training/{model_id}/status")
async def get_training_status(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get training status"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/training/{model_id}/metrics", response_model=TrainingMetricsResponse)
async def get_training_metrics(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get training metrics history"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Evaluation Endpoints
@router.post("/models/{model_id}/evaluate", response_model=EvaluationResult)
async def evaluate_model(model_id: UUID, db: AsyncSession = Depends(get_db)):
    """Evaluate model on test set"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")
