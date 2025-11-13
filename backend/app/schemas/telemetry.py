"""Telemetry focused Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    robot_id: str
    name: str = Field(default="ad-hoc-session")
    metadata: dict[str, Any] | None = None


class SessionResponse(BaseModel):
    id: str
    robot_id: str
    name: str
    is_active: bool
    created_at: datetime
    metadata: dict[str, Any] | None = None


class TelemetryIngest(BaseModel):
    robot_id: str
    sensor_type: str
    payload: dict[str, Any]
    latitude: float | None = None
    longitude: float | None = None
