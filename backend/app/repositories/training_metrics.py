"""Repository for training metrics."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrainingMetric
from app.repositories.base import BaseRepository


class TrainingMetricRepository(BaseRepository):
    """Persist metric snapshots for training runs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_metric(
        self,
        *,
        run_id: uuid.UUID,
        step: int,
        name: str,
        value: float,
    ) -> TrainingMetric:
        metric = TrainingMetric(run_id=run_id, step=step, name=name, value=value)
        return await self.add(metric)

    async def list_for_run(self, run_id: uuid.UUID) -> list[TrainingMetric]:
        stmt = select(TrainingMetric).where(TrainingMetric.run_id == run_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
