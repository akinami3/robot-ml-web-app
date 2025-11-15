"""Telemetry-related application use cases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.application.events import TELEMETRY_CHANNEL, TelemetryEvent
from app.application.interfaces import (
    DatasetSessionRepositoryProtocol,
    SensorDataRepositoryProtocol,
    UnitOfWork,
    WebSocketBroadcaster,
)
from app.core.exceptions import SessionInactiveError
from app.models import DatasetSession


@dataclass(slots=True)
class TelemetryMessage:
    robot_id: str
    sensor_type: str
    payload: dict
    latitude: float | None = None
    longitude: float | None = None


class DataLoggerUseCase:
    """Handles conditional persistence of robot telemetry sessions."""

    def __init__(
        self,
        *,
        unit_of_work: UnitOfWork,
        dataset_repo: DatasetSessionRepositoryProtocol,
        sensor_repo: SensorDataRepositoryProtocol,
    ) -> None:
        self._uow = unit_of_work
        self._dataset_repo = dataset_repo
        self._sensor_repo = sensor_repo

    async def start_session(
        self,
        *,
        robot_id: str,
        name: str,
        metadata: dict | None = None,
    ) -> DatasetSession:
        async with self._uow:
            session = await self._dataset_repo.create(
                name=name,
                robot_id=robot_id,
                metadata=metadata,
            )
        return session

    async def end_session(
        self,
        *,
        session_id: uuid.UUID,
        save: bool = True,
    ) -> None:
        session_obj = await self._dataset_repo.get(session_id)
        if not session_obj:
            return
        async with self._uow:
            if save:
                await self._dataset_repo.mark_inactive(session_id)
            else:
                await self._sensor_repo.delete_for_session(session_id)
                await self._dataset_repo.delete(session_id)

    async def get_active_session(self, robot_id: str) -> DatasetSession | None:
        return await self._dataset_repo.get_active_by_robot(robot_id)

    async def get_active_session_id(self, robot_id: str) -> uuid.UUID | None:
        active = await self.get_active_session(robot_id)
        return active.id if active else None

    async def save_sensor_payload(
        self,
        *,
        robot_id: str,
        sensor_type: str,
        payload: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        session_obj = await self.get_active_session(robot_id)
        if not session_obj:
            raise SessionInactiveError("No active session for robot; telemetry skipped")
        async with self._uow:
            await self._sensor_repo.add_entry(
                session_id=session_obj.id,
                sensor_type=sensor_type,
                payload=payload,
                latitude=latitude,
                longitude=longitude,
            )


class TelemetryProcessorUseCase:
    """Processes incoming telemetry streams and performs conditional persistence."""

    def __init__(
        self,
        *,
        datalogger: DataLoggerUseCase,
        websocket_hub: WebSocketBroadcaster,
    ) -> None:
        self._datalogger = datalogger
        self._ws_hub = websocket_hub

    async def handle_mqtt_message(
        self,
        *,
        robot_id: str,
        sensor_type: str,
        payload: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        try:
            await self._datalogger.save_sensor_payload(
                robot_id=robot_id,
                sensor_type=sensor_type,
                payload=payload,
                latitude=latitude,
                longitude=longitude,
            )
        except SessionInactiveError:
            pass

        await self._ws_hub.broadcast(
            channel=TELEMETRY_CHANNEL,
            message={
                "event": TelemetryEvent.STREAM_UPDATE.value,
                "robot_id": robot_id,
                "sensor_type": sensor_type,
                "payload": payload,
            },
        )

__all__ = [
    "TelemetryMessage",
    "DataLoggerUseCase",
    "TelemetryProcessorUseCase",
]
