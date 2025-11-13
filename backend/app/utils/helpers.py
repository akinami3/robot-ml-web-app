"""Misc utility helpers."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable


async def fire_and_forget(coro: Awaitable[Any]) -> None:
    asyncio.create_task(coro)
