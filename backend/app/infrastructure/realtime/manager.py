"""WebSocket hub for broadcasting messages to subscribed clients."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WebSocketHub:
    """Manages WebSocket connections grouped by logical channel."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections[channel].discard(websocket)

    async def broadcast(self, *, channel: str, message: dict[str, Any]) -> None:
        async with self._lock:
            recipients = list(self._connections.get(channel, set()))
        for connection in recipients:
            await connection.send_json(message)

    async def send_to(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        await websocket.send_json(message)
