"""Telemetry endpoints for session management and ingestion."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_dataset_session_repository,
    get_datalogger_service,
)
from app.core.exceptions import SessionInactiveError
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.schemas.telemetry import SessionCreateRequest, SessionResponse, TelemetryIngest
from app.services.datalogger import DataLoggerService

router = APIRouter()


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: SessionCreateRequest,
    service: DataLoggerService = Depends(get_datalogger_service),
) -> SessionResponse:
    session = await service.start_session(robot_id=request.robot_id, name=request.name, metadata=request.metadata)
    return SessionResponse(
        id=str(session.id),
        robot_id=session.robot_id,
        name=session.name,
        is_active=session.is_active,
        created_at=session.created_at,
        metadata=session.metadata,
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    repo: DatasetSessionRepository = Depends(get_dataset_session_repository),
) -> list[SessionResponse]:
    sessions = await repo.list_sessions()
    return [
        SessionResponse(
            id=str(item.id),
            robot_id=item.robot_id,
            name=item.name,
            is_active=item.is_active,
            created_at=item.created_at,
            metadata=item.metadata,
        )
        for item in sessions
    ]


@router.post("/telemetry", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryIngest,
    service: DataLoggerService = Depends(get_datalogger_service),
) -> dict[str, str]:
    try:
        await service.save_sensor_payload(
            robot_id=payload.robot_id,
            sensor_type=payload.sensor_type,
            payload=payload.payload,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
    except SessionInactiveError:
        return {"status": "ignored"}
    except Exception as exc:  # broad catch to avoid bubbling up to client
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "accepted"}


@router.post("/session/{session_id}/save", status_code=status.HTTP_202_ACCEPTED)
async def save_session(
    session_id: uuid.UUID,
    service: DataLoggerService = Depends(get_datalogger_service),
) -> dict[str, str]:
    await service.end_session(session_id=session_id, save=True)
    return {"status": "saved"}


@router.post("/session/{session_id}/discard", status_code=status.HTTP_202_ACCEPTED)
async def discard_session(
    session_id: uuid.UUID,
    service: DataLoggerService = Depends(get_datalogger_service),
) -> dict[str, str]:
    await service.end_session(session_id=session_id, save=False)
    return {"status": "discarded"}
