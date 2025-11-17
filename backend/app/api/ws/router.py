from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


async def _handle_channel(websocket: WebSocket, channel: str) -> None:
    manager = websocket.app.state.ws_manager
    await manager.connect(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected channel=%s", channel)
    finally:
        await manager.disconnect(channel, websocket)


@router.websocket("/robot")
async def robot_channel(websocket: WebSocket) -> None:
    await _handle_channel(websocket, "robot")


@router.websocket("/telemetry")
async def telemetry_channel(websocket: WebSocket) -> None:
    await _handle_channel(websocket, "telemetry")


@router.websocket("/training")
async def training_channel(websocket: WebSocket) -> None:
    await _handle_channel(websocket, "training")


@router.websocket("/chatbot")
async def chatbot_channel(websocket: WebSocket) -> None:
    await _handle_channel(websocket, "chatbot")
