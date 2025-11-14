"""WebSocket route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_websocket_hub
from app.infrastructure.realtime.manager import WebSocketHub

router = APIRouter()


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    hub: WebSocketHub = Depends(get_websocket_hub),
) -> None:
    await hub.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await hub.broadcast(channel=channel, message=data)
    except WebSocketDisconnect:
        await hub.disconnect(channel, websocket)
