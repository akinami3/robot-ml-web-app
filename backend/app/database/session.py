"""Database session management utilities."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.engine import get_engine

_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (and lazily create) the async session factory."""

    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(), expire_on_commit=False
        )
    return _async_session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an AsyncSession."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
