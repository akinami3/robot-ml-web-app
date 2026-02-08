"""
Pydantic Schemas for API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class RobotState(str, Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    CHARGING = "CHARGING"


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class MissionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ==================== User Schemas ====================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Auth Schemas ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ==================== Robot Schemas ====================

class Position(BaseModel):
    x: float
    y: float
    theta: float = 0.0


class Capabilities(BaseModel):
    supports_pause: bool = True
    supports_docking: bool = False


class RobotBase(BaseModel):
    robot_id: str
    name: str
    vendor: str
    model: Optional[str] = None


class RobotCreate(RobotBase):
    capabilities: Optional[Capabilities] = None


class RobotUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    capabilities: Optional[Capabilities] = None


class RobotStatus(BaseModel):
    """Robot status from Gateway"""
    robot_id: str
    state: RobotState
    battery: float
    pose: Position
    is_online: bool


class RobotResponse(RobotBase):
    id: int
    state: RobotState
    battery: float
    pos_x: float
    pos_y: float
    pos_theta: float
    capabilities: Optional[dict] = None
    is_online: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RobotListResponse(BaseModel):
    total: int
    robots: List[RobotResponse]


# ==================== Mission Schemas ====================

class MissionBase(BaseModel):
    name: str
    goal_x: float
    goal_y: float
    goal_theta: float = 0.0


class MissionCreate(MissionBase):
    robot_id: str


class MissionResponse(MissionBase):
    id: int
    mission_id: str
    robot_id: int
    status: MissionStatus
    created_by: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MissionListResponse(BaseModel):
    total: int
    missions: List[MissionResponse]


# ==================== Command Schemas ====================

class MoveCommand(BaseModel):
    """Command to move robot to position"""
    robot_id: str
    goal: Position


class StopCommand(BaseModel):
    """Command to stop robot"""
    robot_id: str


class CommandResponse(BaseModel):
    success: bool
    message: str
    command_id: Optional[str] = None


# ==================== Log Schemas ====================

class RobotLogResponse(BaseModel):
    id: int
    robot_id: int
    log_type: str
    message: Optional[str] = None
    data: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Health Schemas ====================

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    mqtt: str
