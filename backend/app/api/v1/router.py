"""API v1 router - aggregates all endpoint routers."""

from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.audit import router as audit_router
from .endpoints.datasets import router as datasets_router
from .endpoints.rag import router as rag_router
from .endpoints.recordings import router as recordings_router
from .endpoints.robots import router as robots_router
from .endpoints.sensors import router as sensors_router
from .endpoints.users import router as users_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(robots_router)
api_router.include_router(sensors_router)
api_router.include_router(datasets_router)
api_router.include_router(recordings_router)
api_router.include_router(rag_router)
api_router.include_router(audit_router)
