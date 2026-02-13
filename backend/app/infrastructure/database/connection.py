"""Database connection management."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from ...config import Settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(settings: Settings) -> None:
    """Initialize database engine and session factory."""
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_db() -> None:
    """Close database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield an async database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialized.")
    return _engine
