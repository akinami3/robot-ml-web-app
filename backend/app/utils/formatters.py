"""Formatting helpers."""

from __future__ import annotations

from datetime import datetime


def isoformat(dt: datetime) -> str:
    return dt.astimezone().isoformat()
