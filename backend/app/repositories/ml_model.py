"""
ML model repositories
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ml_model import MLModel, TrainingHistory
from app.repositories.base import BaseRepository


class MLModelRepository(BaseRepository[MLModel]):
    """Repository for ML models"""

    def __init__(self):
        super().__init__(MLModel)

    async def get_by_dataset(self, db: AsyncSession, dataset_id: UUID) -> List[MLModel]:
        """Get models by dataset"""
        result = await db.execute(
            select(MLModel)
            .where(MLModel.dataset_id == dataset_id)
            .order_by(MLModel.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_status(
        self, db: AsyncSession, status: str, skip: int = 0, limit: int = 100
    ) -> List[MLModel]:
        """Get models by training status"""
        result = await db.execute(
            select(MLModel)
            .where(MLModel.training_status == status)
            .order_by(MLModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class TrainingHistoryRepository(BaseRepository[TrainingHistory]):
    """Repository for training history"""

    def __init__(self):
        super().__init__(TrainingHistory)

    async def get_by_model(
        self, db: AsyncSession, model_id: UUID, skip: int = 0, limit: int = 1000
    ) -> List[TrainingHistory]:
        """Get training history for a model"""
        result = await db.execute(
            select(TrainingHistory)
            .where(TrainingHistory.model_id == model_id)
            .order_by(TrainingHistory.epoch.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_epoch(
        self, db: AsyncSession, model_id: UUID
    ) -> Optional[TrainingHistory]:
        """Get latest epoch for a model"""
        result = await db.execute(
            select(TrainingHistory)
            .where(TrainingHistory.model_id == model_id)
            .order_by(TrainingHistory.epoch.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


# Global instances
ml_model_repo = MLModelRepository()
training_history_repo = TrainingHistoryRepository()
