from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any


logger = logging.getLogger(__name__)

MessageHandler = Callable[[str, bytes], Awaitable[None]]


class MQTTClient:
    """Minimal async-safe MQTT facade.

    実機の接続ロジックは後で差し替える想定。現段階では publish/subscribe の
    インターフェースとハンドラ登録のみ保証する。
    """

    def __init__(
        self,
        broker_url: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._broker_url = broker_url
        self._username = username
        self._password = password
        self._connected = asyncio.Event()
        self._handlers: dict[str, MessageHandler] = {}

    async def connect(self) -> None:
        logger.info("Connecting to MQTT broker %s", self._broker_url)
        self._connected.set()

    async def disconnect(self) -> None:
        if not self._connected.is_set():
            return
        logger.info("Disconnecting from MQTT broker %s", self._broker_url)
        self._connected.clear()

    async def publish(self, topic: str, payload: dict[str, Any] | bytes, qos: int = 0) -> None:
        await self._ensure_connected()
        if isinstance(payload, dict):
            serialized = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, bytes):
            serialized = payload
        else:
            raise TypeError("payload must be dict or bytes")
        logger.debug("[MQTT] publish topic=%s qos=%d payload=%s", topic, qos, serialized)
        # 実メッセージ送信は後で実装。ここではログのみ。

    def register_handler(self, topic: str, handler: MessageHandler) -> None:
        self._handlers[topic] = handler
        logger.debug("Registered MQTT handler for topic %s", topic)

    async def dispatch_message(self, topic: str, payload: bytes) -> None:
        await self._ensure_connected()
        handler = self._handlers.get(topic)
        if not handler:
            logger.warning("MQTT message dropped topic=%s no handler", topic)
            return
        await handler(topic, payload)

    async def _ensure_connected(self) -> None:
        if not self._connected.is_set():
            raise RuntimeError("MQTT client is not connected")
