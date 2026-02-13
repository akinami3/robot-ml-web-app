"""
Robot AI Web Application - FastAPI Main Application
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .config import get_settings
from .core.logging import setup_logging
from .infrastructure.database.connection import close_db, get_engine, init_db
from .infrastructure.redis.connection import close_redis, init_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown."""
    settings = get_settings()
    setup_logging(settings.backend_log_level)

    logger.info("Starting Robot AI Backend", environment=settings.environment)

    # Initialize database
    await init_db(settings)
    logger.info("Database initialized")

    # Initialize Redis
    redis_client = await init_redis(settings.redis_url)
    logger.info("Redis connected")

    # Start recording worker
    from .infrastructure.redis.recording_worker import RecordingWorker
    from .infrastructure.database.connection import get_session
    from .infrastructure.database.repositories.recording_repo import (
        SQLAlchemyRecordingRepository,
    )
    from .infrastructure.database.repositories.sensor_data_repo import (
        SQLAlchemySensorDataRepository,
    )
    from .domain.services.recording_service import RecordingService

    # Create a simple worker (simplified - in production you'd use proper DI)
    worker = None
    try:
        # Get a session for the recording service
        session_gen = get_session()
        session = await session_gen.__anext__()
        recording_repo = SQLAlchemyRecordingRepository(session)
        sensor_repo = SQLAlchemySensorDataRepository(session)
        recording_svc = RecordingService(recording_repo, sensor_repo)

        worker = RecordingWorker(
            redis_client=redis_client,
            recording_service=recording_svc,
        )
        await worker.start()
        logger.info("Recording worker started")
    except Exception as e:
        logger.warning("Recording worker failed to start", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down...")
    if worker is not None:
        await worker.stop()
    await close_redis()
    await close_db()
    logger.info("Backend stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Robot AI Web Application API",
        description="API for robot control, sensor data management, ML datasets, and RAG",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    # Health check
    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "healthy", "service": "backend"}

    @app.get("/ready")
    async def readiness_check() -> dict:
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return {"status": "ready"}
        except Exception:
            return {"status": "not_ready"}

    return app


app = create_app()
