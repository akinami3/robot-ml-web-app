"""Repository for dataset sessions."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DatasetSession
from app.repositories.base import BaseRepository


class DatasetSessionRepository(BaseRepository):
    """Persist and query dataset sessions."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create(self, *, name: str, robot_id: str, metadata: dict | None = None) -> DatasetSession:
        session = DatasetSession(name=name, robot_id=robot_id, metadata=metadata)
        await self.add(session)
        return session

    async def get_active_by_robot(self, robot_id: str) -> DatasetSession | None:
        stmt = (
            select(DatasetSession)
            .where(DatasetSession.robot_id == robot_id)
            .where(DatasetSession.is_active.is_(True))
            .order_by(DatasetSession.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def mark_inactive(self, session_id: uuid.UUID) -> None:
        stmt = (
            update(DatasetSession)
            .where(DatasetSession.id == session_id)
            .values(is_active=False)
        )
        await self.session.execute(stmt)

    async def get(self, session_id: uuid.UUID) -> DatasetSession | None:
        stmt = select(DatasetSession).where(DatasetSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete(self, session_id: uuid.UUID) -> None:
        session_obj = await self.get(session_id)
        if session_obj:
            await self.session.delete(session_obj)

    async def list_sessions(self, *, active_only: bool | None = None) -> list[DatasetSession]:
        stmt = select(DatasetSession)
        if active_only is True:
            stmt = stmt.where(DatasetSession.is_active.is_(True))
        elif active_only is False:
            stmt = stmt.where(DatasetSession.is_active.is_(False))
        stmt = stmt.order_by(DatasetSession.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
