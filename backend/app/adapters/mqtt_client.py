"""Async MQTT client adapter built on top of asyncio-mqtt."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Any

from asyncio_mqtt import Client, MqttError

from app.core.config import settings

MessageCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


class MQTTClientAdapter:
    """Thin wrapper that provides publish/subscribe helpers."""

    def __init__(self) -> None:
        self._client = Client(
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            client_id=settings.mqtt_client_id,
        )
        self._connected = False
        self._stack = AsyncExitStack()
        self._listener_tasks: set[asyncio.Task[None]] = set()

    async def connect(self) -> None:
        if self._connected:
            return
        await self._stack.enter_async_context(self._client)
        self._connected = True

    async def disconnect(self) -> None:
        if not self._connected:
            return
        while self._listener_tasks:
            task = self._listener_tasks.pop()
            task.cancel()
        await self._stack.aclose()
        self._connected = False

    async def publish(self, topic: str, payload: dict[str, Any], qos: int = 1) -> None:
        await self.connect()
        await self._client.publish(topic, json.dumps(payload), qos=qos)

    async def subscribe_with_callback(self, topic: str, callback: MessageCallback) -> None:
        await self.connect()
        manager = self

        async def _listener() -> None:
            async with self._client.filtered_messages(topic) as messages:
                await self._client.subscribe(topic)
                async for message in messages:
                    try:
                        decoded = json.loads(message.payload.decode("utf-8"))
                    except json.JSONDecodeError:
                        decoded = {"raw": message.payload.decode("utf-8")}
                    await callback(message.topic, decoded)

        task = asyncio.create_task(_listener())
        manager._listener_tasks.add(task)
        task.add_done_callback(manager._listener_tasks.discard)


__all__ = ["MQTTClientAdapter"]
