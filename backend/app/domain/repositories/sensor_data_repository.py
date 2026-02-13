"""Sensor data repository interface."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from ..entities.sensor_data import SensorData, SensorType
from .base import BaseRepository


class SensorDataRepository(BaseRepository[SensorData]):
    @abstractmethod
    async def get_by_robot(
        self,
        robot_id: UUID,
        sensor_type: SensorType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[SensorData]:
        ...

    @abstractmethod
    async def get_by_session(
        self,
        session_id: UUID,
        sensor_type: SensorType | None = None,
    ) -> list[SensorData]:
        ...

    @abstractmethod
    async def bulk_insert(self, data: list[SensorData]) -> int:
        ...

    @abstractmethod
    async def get_latest(
        self, robot_id: UUID, sensor_type: SensorType
    ) -> SensorData | None:
        ...

    @abstractmethod
    async def count_by_session(self, session_id: UUID) -> int:
        ...

    @abstractmethod
    async def delete_older_than(self, before: datetime) -> int:
        ...

    @abstractmethod
    async def get_aggregated(
        self,
        robot_id: UUID,
        sensor_type: SensorType,
        start_time: datetime,
        end_time: datetime,
        bucket_seconds: int = 60,
    ) -> list[dict]:
        ...
