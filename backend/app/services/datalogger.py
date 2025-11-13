"""Data logging orchestration service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionInactiveError
from app.models import DatasetSession
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.repositories.sensor_data import SensorDataRepository


class DataLoggerService:
    """Handles conditional persistence of robot telemetry."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        dataset_repo: DatasetSessionRepository,
        sensor_repo: SensorDataRepository,
    ) -> None:
        self._session = session
        self._dataset_repo = dataset_repo
        self._sensor_repo = sensor_repo

    async def start_session(self, *, robot_id: str, name: str, metadata: dict | None = None) -> DatasetSession:
        session = await self._dataset_repo.create(name=name, robot_id=robot_id, metadata=metadata)
        await self._session.commit()
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
        if save:
            await self._dataset_repo.mark_inactive(session_id)
        else:
            await self._dataset_repo.mark_inactive(session_id)
            # Additional cleanup (delete sensor data) could be implemented here
        await self._session.commit()

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
        await self._sensor_repo.add_entry(
            session_id=session_obj.id,
            sensor_type=sensor_type,
            payload=payload,
            latitude=latitude,
            longitude=longitude,
        )
        await self._session.commit()
