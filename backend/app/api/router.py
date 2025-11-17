"""
Main API router
Aggregates all API version 1 routers
"""
from fastapi import APIRouter

from app.api.v1 import chatbot, database, ml, robot_control, websocket

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(robot_control.router, prefix="/robot-control", tags=["Robot Control"])
api_router.include_router(database.router, prefix="/database", tags=["Database"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
