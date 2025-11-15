"""SQLAlchemy-backed unit of work implementation."""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Wraps an `AsyncSession` to provide transaction helpers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._transaction_ctx: Optional[AbstractAsyncContextManager] = None

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        if self._transaction_ctx is not None:
            raise RuntimeError("UnitOfWork transaction already active")
        ctx = self._session.begin()
        self._transaction_ctx = ctx
        await ctx.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ctx = self._transaction_ctx
        if ctx is None:
            return
        try:
            await ctx.__aexit__(exc_type, exc_value, traceback)
        finally:
            self._transaction_ctx = None

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


__all__ = ["SqlAlchemyUnitOfWork"]
