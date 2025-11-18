"""
Dataset-related repositories
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, RecordingSession, RobotDataPoint
from app.repositories.base import BaseRepository


class RecordingSessionRepository(BaseRepository[RecordingSession]):
    """Repository for recording sessions"""

    def __init__(self):
        super().__init__(RecordingSession)

    async def get_active(self, db: AsyncSession) -> Optional[RecordingSession]:
        """Get active recording session"""
        result = await db.execute(
            select(RecordingSession)
            .where(RecordingSession.status.in_(["recording", "paused"]))
            .order_by(RecordingSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self, db: AsyncSession, status: str, skip: int = 0, limit: int = 100
    ) -> List[RecordingSession]:
        """Get sessions by status"""
        result = await db.execute(
            select(RecordingSession)
            .where(RecordingSession.status == status)
            .order_by(RecordingSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class RobotDataPointRepository(BaseRepository[RobotDataPoint]):
    """Repository for robot data points"""

    def __init__(self):
        super().__init__(RobotDataPoint)

    async def get_by_session(
        self, db: AsyncSession, session_id: UUID, skip: int = 0, limit: int = 1000
    ) -> List[RobotDataPoint]:
        """Get data points for a session"""
        result = await db.execute(
            select(RobotDataPoint)
            .where(RobotDataPoint.session_id == session_id)
            .order_by(RobotDataPoint.timestamp.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_session(self, db: AsyncSession, session_id: UUID) -> int:
        """Count data points in a session"""
        result = await db.execute(
            select(RobotDataPoint).where(RobotDataPoint.session_id == session_id)
        )
        return len(result.scalars().all())


class DatasetRepository(BaseRepository[Dataset]):
    """Repository for datasets"""

    def __init__(self):
        super().__init__(Dataset)

    async def get_by_session(self, db: AsyncSession, session_id: UUID) -> List[Dataset]:
        """Get datasets created from a session"""
        result = await db.execute(
            select(Dataset)
            .where(Dataset.session_id == session_id)
            .order_by(Dataset.created_at.desc())
        )
        return result.scalars().all()


# Global instances
recording_session_repo = RecordingSessionRepository()
robot_data_point_repo = RobotDataPointRepository()
dataset_repo = DatasetRepository()
