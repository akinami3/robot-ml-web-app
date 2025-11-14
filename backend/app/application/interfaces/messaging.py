"""Interfaces for messaging backends (e.g., MQTT)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

MessageCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


class MQTTPublisher(Protocol):
    """Protocol for publishing messages to MQTT topics."""

    async def publish(self, topic: str, payload: dict[str, Any], qos: int = ...) -> None: ...

    async def subscribe_with_callback(self, topic: str, callback: MessageCallback) -> None: ...
