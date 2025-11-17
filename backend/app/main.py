"""
FastAPI main application
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog import get_logger

from app.api.router import api_router
from app.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import RobotMLException
from app.core.logger import configure_logging
from app.core.mqtt import mqtt_client
from app.core.websocket import heartbeat_task, ws_manager

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("application_starting", env=settings.APP_ENV)

    # Initialize database
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_error", error=str(e))

    # Connect to MQTT broker
    try:
        await mqtt_client.connect()
        logger.info("mqtt_connected")
    except Exception as e:
        logger.error("mqtt_connect_error", error=str(e))

    # Start WebSocket heartbeat task
    heartbeat_handle = asyncio.create_task(
        heartbeat_task(ws_manager, interval=settings.WS_HEARTBEAT_INTERVAL)
    )

    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Cancel heartbeat task
    heartbeat_handle.cancel()
    try:
        await heartbeat_handle
    except asyncio.CancelledError:
        pass

    # Disconnect MQTT
    try:
        await mqtt_client.disconnect()
        logger.info("mqtt_disconnected")
    except Exception as e:
        logger.error("mqtt_disconnect_error", error=str(e))

    # Close database connections
    try:
        await close_db()
        logger.info("database_closed")
    except Exception as e:
        logger.error("database_close_error", error=str(e))

    logger.info("application_stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Robot ML Web Application",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RobotMLException)
async def robot_ml_exception_handler(request, exc: RobotMLException):
    """Handle custom application exceptions"""
    logger.error(
        "application_error",
        error=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": type(exc).__name__},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error("uncaught_exception", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "type": "InternalServerError"},
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.connected,
        "websocket_connections": ws_manager.get_connection_count(),
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
