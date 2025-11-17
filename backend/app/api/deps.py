"""
API dependencies
"""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mqtt import mqtt_client
from app.core.websocket import ws_manager
from app.dependencies import get_db


async def get_mqtt_client():
    """Get MQTT client dependency"""
    return mqtt_client


async def get_ws_manager():
    """Get WebSocket manager dependency"""
    return ws_manager
