"""Recording session endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ....domain.entities.audit_log import AuditAction
from ....domain.entities.recording import RecordingConfig
from ....domain.entities.sensor_data import SensorType
from ..dependencies import AuditSvc, CurrentUser, OperatorUser, RecordingSvc
from ..schemas import RecordingResponse, RecordingStartRequest

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("", response_model=RecordingResponse, status_code=201)
async def start_recording(
    body: RecordingStartRequest,
    current_user: OperatorUser,
    recording_svc: RecordingSvc,
    audit_svc: AuditSvc,
):
    sensor_types = []
    for st_str in body.sensor_types:
        try:
            sensor_types.append(SensorType(st_str))
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid sensor type: {st_str}"
            )

    max_freq = {}
    for st_str, freq in body.max_frequency_hz.items():
        try:
            max_freq[SensorType(st_str)] = freq
        except ValueError:
            pass

    config = RecordingConfig(
        sensor_types=sensor_types,
        max_frequency_hz=max_freq,
    )

    try:
        session = await recording_svc.start_recording(
            robot_id=body.robot_id,
            user_id=current_user.id,
            config=config,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RECORDING_START,
        resource_type="recording",
        resource_id=str(session.id),
        details={
            "robot_id": str(body.robot_id),
            "sensor_types": body.sensor_types,
        },
    )

    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )


@router.post("/{session_id}/stop", response_model=RecordingResponse)
async def stop_recording(
    session_id: UUID,
    current_user: OperatorUser,
    recording_svc: RecordingSvc,
    audit_svc: AuditSvc,
):
    session = await recording_svc.stop_recording(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Recording session not found")

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.RECORDING_STOP,
        resource_type="recording",
        resource_id=str(session_id),
        details={"record_count": session.record_count},
    )

    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )


@router.get("", response_model=list[RecordingResponse])
async def list_recordings(
    current_user: CurrentUser,
    recording_svc: RecordingSvc,
):
    sessions = await recording_svc.get_user_sessions(current_user.id)
    return [
        RecordingResponse(
            id=s.id,
            robot_id=s.robot_id,
            user_id=s.user_id,
            is_active=s.is_active,
            record_count=s.record_count,
            size_bytes=s.size_bytes,
            started_at=s.started_at,
            stopped_at=s.stopped_at,
            config={
                "sensor_types": [st.value for st in s.config.sensor_types],
                "enabled": s.config.enabled,
            },
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=RecordingResponse)
async def get_recording(
    session_id: UUID,
    current_user: CurrentUser,
    recording_svc: RecordingSvc,
):
    session = await recording_svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Recording session not found")

    return RecordingResponse(
        id=session.id,
        robot_id=session.robot_id,
        user_id=session.user_id,
        is_active=session.is_active,
        record_count=session.record_count,
        size_bytes=session.size_bytes,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        config={
            "sensor_types": [st.value for st in session.config.sensor_types],
            "enabled": session.config.enabled,
        },
    )
