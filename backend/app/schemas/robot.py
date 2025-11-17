"""
Pydantic schemas for robot control
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Velocity Command Schemas
class VelocityCommand(BaseModel):
    """Velocity command schema"""

    vx: float = Field(..., description="Linear velocity X (m/s)")
    vy: float = Field(0.0, description="Linear velocity Y (m/s)")
    vz: float = Field(0.0, description="Linear velocity Z (m/s)")
    angular: float = Field(..., description="Angular velocity (rad/s)")


# Navigation Schemas
class NavigationGoalCreate(BaseModel):
    """Create navigation goal"""

    goal_name: Optional[str] = Field(None, max_length=100)
    target_x: float
    target_y: float
    target_z: float = 0.0
    orientation_x: Optional[float] = None
    orientation_y: Optional[float] = None
    orientation_z: Optional[float] = None
    orientation_w: Optional[float] = None


class NavigationGoalResponse(BaseModel):
    """Navigation goal response"""

    id: UUID
    goal_name: Optional[str]
    target_x: float
    target_y: float
    target_z: float
    status: str
    progress: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Robot Status Schemas
class RobotStatusResponse(BaseModel):
    """Robot status response"""

    id: UUID
    timestamp: datetime
    position_x: Optional[float]
    position_y: Optional[float]
    position_z: Optional[float]
    orientation_x: Optional[float]
    orientation_y: Optional[float]
    orientation_z: Optional[float]
    orientation_w: Optional[float]
    velocity_x: Optional[float]
    velocity_y: Optional[float]
    velocity_z: Optional[float]
    angular_velocity: Optional[float]
    battery_level: Optional[float]
    connection_status: Optional[str]
    error_message: Optional[str]
    extra_data: Optional[dict]

    class Config:
        from_attributes = True


# Simulator Schemas
class SimulatorStatus(BaseModel):
    """Simulator status response"""

    is_running: bool
    process_id: Optional[int]
    started_at: Optional[datetime]
