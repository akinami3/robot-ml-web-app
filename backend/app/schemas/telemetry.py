from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.infrastructure.database.models.telemetry_session import TelemetrySessionStatus


class TelemetrySessionCreate(BaseModel):
    device_id: UUID
    name: str
    capture_velocity: bool = True
    capture_state: bool = True
    capture_images: bool = False
    session_metadata: dict | None = None


class TelemetrySessionUpdate(BaseModel):
    status: TelemetrySessionStatus


class TelemetrySession(BaseModel):
    id: UUID
    device_id: UUID
    name: str
    status: TelemetrySessionStatus
    capture_velocity: bool
    capture_state: bool
    capture_images: bool
    session_metadata: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TelemetryRecordIn(BaseModel):
    session_id: UUID
    timestamp: datetime
    linear_velocity_x: float | None = None
    linear_velocity_y: float | None = None
    angular_velocity_z: float | None = None
    state: dict | None = None
    notes: str | None = Field(default=None, max_length=256)
