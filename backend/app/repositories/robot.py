"""
Robot-related repositories
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.robot import NavigationGoal, RobotStatus
from app.repositories.base import BaseRepository


class RobotStatusRepository(BaseRepository[RobotStatus]):
    """Repository for robot status"""

    def __init__(self, db: AsyncSession):
        super().__init__(RobotStatus, db)

    async def get_latest(self) -> Optional[RobotStatus]:
        """Get latest robot status"""
        result = await self.db.execute(
            select(RobotStatus).order_by(RobotStatus.timestamp.desc()).limit(1)
        )
        return result.scalar_one_or_none()


class NavigationGoalRepository(BaseRepository[NavigationGoal]):
    """Repository for navigation goals"""

    def __init__(self, db: AsyncSession):
        super().__init__(NavigationGoal, db)

    async def get_active(self) -> Optional[NavigationGoal]:
        """Get active navigation goal"""
        result = await self.db.execute(
            select(NavigationGoal)
            .where(NavigationGoal.status.in_(["pending", "active"]))
            .order_by(NavigationGoal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def cancel_active(self) -> None:
        """Cancel all active navigation goals"""
        result = await self.db.execute(
            select(NavigationGoal).where(NavigationGoal.status.in_(["pending", "active"]))
        )
        goals = result.scalars().all()
        for goal in goals:
            goal.status = "cancelled"
        await self.db.commit()

