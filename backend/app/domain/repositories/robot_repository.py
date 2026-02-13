"""Robot repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from ..entities.robot import Robot, RobotState
from .base import BaseRepository


class RobotRepository(BaseRepository[Robot]):
    @abstractmethod
    async def get_by_name(self, name: str) -> Robot | None:
        ...

    @abstractmethod
    async def get_by_state(self, state: RobotState) -> list[Robot]:
        ...

    @abstractmethod
    async def update_state(self, robot_id: UUID, state: RobotState) -> bool:
        ...

    @abstractmethod
    async def update_battery(self, robot_id: UUID, level: float) -> bool:
        ...
