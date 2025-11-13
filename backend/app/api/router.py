"""Root API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.chatbot.router import router as chatbot_router
from app.api.ml.router import router as ml_router
from app.api.robot_api.router import router as robot_router
from app.api.telemetry.router import router as telemetry_router

api_router = APIRouter()

api_router.include_router(robot_router, prefix="/robot", tags=["robot"])
api_router.include_router(telemetry_router, prefix="/datalogger", tags=["telemetry"])
api_router.include_router(ml_router, prefix="/ml", tags=["ml"])
api_router.include_router(chatbot_router, prefix="/chat", tags=["chat"])
