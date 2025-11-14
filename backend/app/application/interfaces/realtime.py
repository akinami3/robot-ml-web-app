"""Interfaces for realtime broadcasting components."""

from __future__ import annotations

from typing import Any, Protocol


class WebSocketBroadcaster(Protocol):
    """Protocol for broadcasting messages to connected websocket clients."""

    async def broadcast(self, *, channel: str, message: dict[str, Any]) -> None: ...
