"""Robot feature schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VelocityCommand(BaseModel):
    robot_id: str = Field(..., description="Target robot identifier")
    linear: float = Field(..., description="Linear velocity (m/s)")
    angular: float = Field(..., description="Angular velocity (rad/s)")


class NavigationGoal(BaseModel):
    robot_id: str
    target_x: float
    target_y: float
    orientation: float


class SimulationToggleRequest(BaseModel):
    robot_id: str
    enable: bool
    metadata: dict | None = None


class RobotCommandResponse(BaseModel):
    status: str = "accepted"
