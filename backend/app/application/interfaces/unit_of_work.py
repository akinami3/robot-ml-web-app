"""Abstractions for transactional unit-of-work handling."""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Protocol):
    """Represents a transactional boundary for use cases."""

    @property
    def session(self) -> AsyncSession: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

