"""Database engine configuration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return singleton async engine instance."""

    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=False, future=True)
    return _engine
