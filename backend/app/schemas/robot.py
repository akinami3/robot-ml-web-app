from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.infrastructure.database.models.robot_device import RobotDeviceType


class VelocityCommand(BaseModel):
    linear_x: float = Field(..., alias="vx")
    linear_y: float = Field(..., alias="vy")
    angular_z: float = Field(..., alias="omega")

    class Config:
        allow_population_by_field_name = True


class NavigationGoal(BaseModel):
    target_x: float
    target_y: float
    target_yaw: float


class NavigationCommand(BaseModel):
    goal: NavigationGoal
    frame_id: str = "map"


class RobotDevice(BaseModel):
    id: UUID
    name: str
    identifier: str
    kind: RobotDeviceType
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
