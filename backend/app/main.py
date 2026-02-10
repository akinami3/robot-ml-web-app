"""
AMR SaaS Platform - Backend Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

import asyncio

from app.config import get_settings
from app.database import init_db
from app.routers import auth_router, robots_router, missions_router, sensor_data_router
from app.schemas import HealthResponse

settings = get_settings()

# Redis client
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global redis_client
    
    # Startup
    print("Starting up...")
    await init_db()
    
    # Initialize Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None
    
    # Start gRPC server for data recording from Gateway
    grpc_task = None
    try:
        from app.grpc_server import start_grpc_server
        grpc_task = asyncio.create_task(start_grpc_server())
        print(f"Data recording gRPC server started on port {settings.GRPC_SERVER_PORT}")
    except Exception as e:
        print(f"Failed to start gRPC server: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    if grpc_task:
        grpc_task.cancel()
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AMR Fleet Management SaaS Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(robots_router, prefix="/api/v1")
app.include_router(missions_router, prefix="/api/v1")
app.include_router(sensor_data_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    
    # Check database
    db_status = "healthy"
    try:
        from sqlalchemy import text
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis
    redis_status = "healthy"
    try:
        if redis_client:
            await redis_client.ping()
        else:
            redis_status = "disconnected"
    except Exception:
        redis_status = "unhealthy"
    
    # Check Gateway via gRPC
    gateway_status = "unknown"
    try:
        from app.grpc_client import get_gateway_client
        client = get_gateway_client()
        await client.connect()
        result = await client.health_check()
        gateway_status = "healthy" if result.get("healthy") else "unhealthy"
    except Exception:
        gateway_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status,
        mqtt=gateway_status
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
