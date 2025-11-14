"""ML feature schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TrainingConfig(BaseModel):
    model_name: str
    robot_id: str
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    dataset_session_id: uuid.UUID | None = None


class TrainingLaunchResponse(BaseModel):
    run_id: uuid.UUID
    status: str = "queued"


class TrainingMetricSnapshot(BaseModel):
    step: int
    name: str
    value: float
    timestamp: datetime
