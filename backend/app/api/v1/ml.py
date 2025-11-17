from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_ws_manager
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from app.schemas.training import TrainingJob, TrainingJobCreate
from app.services.training_service import TrainingService
from app.workers.training_worker import TrainingTask, TrainingWorker

router = APIRouter(prefix="/ml", tags=["ml"])


_worker_instance: TrainingWorker | None = None


def get_training_service(
    db: Session = Depends(get_db),
    ws_manager: WebSocketConnectionManager = Depends(get_ws_manager),
) -> TrainingService:
    return TrainingService(db, ws_manager)


def get_training_worker(
    ws_manager: WebSocketConnectionManager = Depends(get_ws_manager),
) -> TrainingWorker:
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = TrainingWorker(ws_manager)
        asyncio.create_task(_worker_instance.run_forever())
    return _worker_instance


@router.post("/jobs", response_model=TrainingJob)
def create_job(
    payload: TrainingJobCreate,
    service: TrainingService = Depends(get_training_service),
    worker: TrainingWorker = Depends(get_training_worker),
) -> TrainingJob:
    job = service.create_job(payload)
    task = TrainingTask(job_id=job.id, epochs=payload.config.get("epochs", 3))
    asyncio.create_task(worker.enqueue(task))
    return job


@router.get("/jobs", response_model=list[TrainingJob])
def list_jobs(service: TrainingService = Depends(get_training_service)) -> list[TrainingJob]:
    return service.list_jobs()
