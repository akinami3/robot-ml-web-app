"""Repository for sensor data entries."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SensorData
from app.repositories.base import BaseRepository


class SensorDataRepository(BaseRepository):
    """Persist sensor payloads."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_entry(
        self,
        *,
        session_id: uuid.UUID,
        sensor_type: str,
        payload: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> SensorData:
        entry = SensorData(
            session_id=session_id,
            sensor_type=sensor_type,
            payload=payload,
            latitude=latitude,
            longitude=longitude,
        )
        return await self.add(entry)

    async def list_by_session(self, session_id: uuid.UUID) -> list[SensorData]:
        stmt = select(SensorData).where(SensorData.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_for_session(self, session_id: uuid.UUID) -> None:
        stmt = delete(SensorData).where(SensorData.session_id == session_id)
        await self.session.execute(stmt)
