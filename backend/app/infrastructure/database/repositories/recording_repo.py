"""SQLAlchemy implementation of RecordingRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.recording import RecordingConfig, RecordingSession
from ....domain.entities.sensor_data import SensorType
from ....domain.repositories.recording_repository import RecordingRepository
from ..models import RecordingSessionModel


class SQLAlchemyRecordingRepository(RecordingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _config_to_dict(self, config: RecordingConfig) -> dict:
        return {
            "sensor_types": [st.value for st in config.sensor_types],
            "max_frequency_hz": {
                st.value: freq for st, freq in config.max_frequency_hz.items()
            },
            "enabled": config.enabled,
        }

    def _config_from_dict(self, data: dict) -> RecordingConfig:
        sensor_types = []
        for st_str in data.get("sensor_types", []):
            try:
                sensor_types.append(SensorType(st_str))
            except ValueError:
                pass
        max_freq = {}
        for st_str, freq in data.get("max_frequency_hz", {}).items():
            try:
                max_freq[SensorType(st_str)] = freq
            except ValueError:
                pass
        return RecordingConfig(
            sensor_types=sensor_types,
            max_frequency_hz=max_freq,
            enabled=data.get("enabled", True),
        )

    def _to_entity(self, model: RecordingSessionModel) -> RecordingSession:
        return RecordingSession(
            id=model.id,
            robot_id=model.robot_id,
            user_id=model.user_id,
            config=self._config_from_dict(model.config or {}),
            is_active=model.is_active,
            record_count=model.record_count,
            size_bytes=model.size_bytes,
            started_at=model.started_at,
            stopped_at=model.stopped_at,
            dataset_id=model.dataset_id,
        )

    async def get_by_id(self, id: UUID) -> RecordingSession | None:
        result = await self._session.get(RecordingSessionModel, id)
        return self._to_entity(result) if result else None

    async def get_all(
        self, offset: int = 0, limit: int = 100
    ) -> list[RecordingSession]:
        stmt = (
            select(RecordingSessionModel)
            .order_by(RecordingSessionModel.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: RecordingSession) -> RecordingSession:
        model = RecordingSessionModel(
            id=entity.id,
            robot_id=entity.robot_id,
            user_id=entity.user_id,
            config=self._config_to_dict(entity.config),
            is_active=entity.is_active,
            record_count=entity.record_count,
            size_bytes=entity.size_bytes,
            dataset_id=entity.dataset_id,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: RecordingSession) -> RecordingSession:
        model = await self._session.get(RecordingSessionModel, entity.id)
        if model is None:
            raise ValueError(f"Recording session {entity.id} not found")
        model.is_active = entity.is_active
        model.record_count = entity.record_count
        model.size_bytes = entity.size_bytes
        model.stopped_at = entity.stopped_at
        model.dataset_id = entity.dataset_id
        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(RecordingSessionModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(RecordingSessionModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_active_by_robot(
        self, robot_id: UUID
    ) -> RecordingSession | None:
        stmt = (
            select(RecordingSessionModel)
            .where(
                RecordingSessionModel.robot_id == robot_id,
                RecordingSessionModel.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_active_by_user(
        self, user_id: UUID
    ) -> list[RecordingSession]:
        stmt = (
            select(RecordingSessionModel)
            .where(
                RecordingSessionModel.user_id == user_id,
                RecordingSessionModel.is_active.is_(True),
            )
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_robot(
        self, robot_id: UUID
    ) -> list[RecordingSession]:
        stmt = (
            select(RecordingSessionModel)
            .where(RecordingSessionModel.robot_id == robot_id)
            .order_by(RecordingSessionModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def stop_session(self, session_id: UUID) -> bool:
        from datetime import datetime
        stmt = (
            update(RecordingSessionModel)
            .where(RecordingSessionModel.id == session_id)
            .values(is_active=False, stopped_at=datetime.utcnow())
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def update_stats(
        self, session_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        stmt = (
            update(RecordingSessionModel)
            .where(RecordingSessionModel.id == session_id)
            .values(record_count=record_count, size_bytes=size_bytes)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
