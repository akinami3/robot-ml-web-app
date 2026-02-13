"""Recording session repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from ..entities.recording import RecordingSession
from .base import BaseRepository


class RecordingRepository(BaseRepository[RecordingSession]):
    @abstractmethod
    async def get_active_by_robot(self, robot_id: UUID) -> RecordingSession | None:
        ...

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID) -> list[RecordingSession]:
        ...

    @abstractmethod
    async def get_by_robot(self, robot_id: UUID) -> list[RecordingSession]:
        ...

    @abstractmethod
    async def stop_session(self, session_id: UUID) -> bool:
        ...

    @abstractmethod
    async def update_stats(
        self, session_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        ...
