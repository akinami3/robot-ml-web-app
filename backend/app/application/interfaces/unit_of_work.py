"""Abstractions for transactional unit-of-work handling."""

from __future__ import annotations

from __future__ import annotations

from types import TracebackType
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork(Protocol):
    """Represents a transactional boundary for use cases."""

    @property
    def session(self) -> AsyncSession: ...

    async def __aenter__(self) -> "UnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

