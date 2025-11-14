"""SQLAlchemy-backed unit of work implementation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Wraps an `AsyncSession` to provide transaction helpers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


__all__ = ["SqlAlchemyUnitOfWork"]
