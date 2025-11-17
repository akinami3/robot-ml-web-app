from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._locks[channel]:
            self._connections[channel].add(websocket)
        logger.debug("WebSocket connected channel=%s active=%d", channel, len(self._connections[channel]))

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._locks[channel]:
            self._connections[channel].discard(websocket)
        logger.debug("WebSocket disconnected channel=%s active=%d", channel, len(self._connections[channel]))

    async def broadcast(self, channel: str, payload: Any) -> None:
        if channel not in self._connections:
            return
        disconnected: list[WebSocket] = []
        for connection in list(self._connections[channel]):
            try:
                await connection.send_json(payload)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as exc:  # noqa: BLE001
                logger.warning("WebSocket broadcast failed channel=%s: %s", channel, exc)
        for connection in disconnected:
            await self.disconnect(channel, connection)

    async def send(self, websocket: WebSocket, payload: Any) -> None:
        await websocket.send_json(payload)
