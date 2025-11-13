"""Repository for robot state records."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RobotState
from app.repositories.base import BaseRepository


class RobotStateRepository(BaseRepository):
    """Persist robot state snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_state(
        self,
        *,
        robot_id: str,
        status: str,
        battery_level: int,
        session_id: uuid.UUID | None,
        last_error: str | None = None,
    ) -> RobotState:
        state = RobotState(
            robot_id=robot_id,
            status=status,
            battery_level=battery_level,
            session_id=session_id,
            last_error=last_error,
        )
        return await self.add(state)

    async def get_latest(self, robot_id: str) -> RobotState | None:
        stmt = (
            select(RobotState)
            .where(RobotState.robot_id == robot_id)
            .order_by(RobotState.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
