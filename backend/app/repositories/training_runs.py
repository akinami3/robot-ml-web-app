"""Repository for training runs."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrainingRun
from app.repositories.base import BaseRepository


class TrainingRunRepository(BaseRepository):
    """Create and update training runs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_run(
        self,
        *,
        model_name: str,
        dataset_session_id: uuid.UUID | None,
        params: dict | None = None,
    ) -> TrainingRun:
        run = TrainingRun(
            model_name=model_name,
            dataset_session_id=dataset_session_id,
            params=params,
        )
        return await self.add(run)

    async def update_status(self, run_id: uuid.UUID, *, status: str) -> None:
        stmt = update(TrainingRun).where(TrainingRun.id == run_id).values(status=status)
        await self.session.execute(stmt)

    async def get(self, run_id: uuid.UUID) -> TrainingRun | None:
        stmt = select(TrainingRun).where(TrainingRun.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
