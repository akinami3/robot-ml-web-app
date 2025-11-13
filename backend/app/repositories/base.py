"""Base repository classes."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Common functionality for repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, instance: object) -> object:
        self.session.add(instance)
        await self.session.flush()
        return instance
