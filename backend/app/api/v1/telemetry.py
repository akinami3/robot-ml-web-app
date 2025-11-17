from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.infrastructure.storage.media_manager import MediaManager
from app.schemas.telemetry import TelemetryRecordIn, TelemetrySession, TelemetrySessionCreate, TelemetrySessionUpdate
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def get_service(db: Session = Depends(get_db)) -> TelemetryService:
    return TelemetryService(db, media_manager=MediaManager())


@router.post("/sessions", response_model=TelemetrySession)
def create_session(
    payload: TelemetrySessionCreate,
    service: TelemetryService = Depends(get_service),
) -> TelemetrySession:
    return service.create_session(payload)


@router.get("/sessions", response_model=list[TelemetrySession])
def list_sessions(service: TelemetryService = Depends(get_service)) -> list[TelemetrySession]:
    return service.list_sessions()


@router.patch("/sessions/{session_id}", response_model=TelemetrySession)
def update_session(
    session_id: UUID,
    payload: TelemetrySessionUpdate,
    service: TelemetryService = Depends(get_service),
) -> TelemetrySession:
    return service.set_status(session_id, payload.status)


@router.post("/records")
async def ingest_record(
    payload: TelemetryRecordIn,
    service: TelemetryService = Depends(get_service),
):
    await service.buffer_record(payload)
    return {"status": "queued"}
