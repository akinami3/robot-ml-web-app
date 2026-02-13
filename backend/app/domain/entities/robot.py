"""Robot domain entity."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class RobotState(str, enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    IDLE = "idle"
    MOVING = "moving"
    ERROR = "error"
    EMERGENCY_STOPPED = "emergency_stopped"


class RobotCapability(str, enum.Enum):
    VELOCITY_CONTROL = "velocity_control"
    NAVIGATION = "navigation"
    LIDAR = "lidar"
    CAMERA = "camera"
    IMU = "imu"
    ODOMETRY = "odometry"
    BATTERY_MONITOR = "battery_monitor"
    GPS = "gps"
    ARM_CONTROL = "arm_control"


@dataclass
class Robot:
    name: str
    adapter_type: str
    id: UUID = field(default_factory=uuid4)
    state: RobotState = RobotState.DISCONNECTED
    capabilities: list[RobotCapability] = field(default_factory=list)
    connection_params: dict[str, Any] = field(default_factory=dict)
    battery_level: float | None = None
    last_seen: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_connected(self) -> bool:
        return self.state not in (RobotState.DISCONNECTED, RobotState.CONNECTING)

    @property
    def is_emergency_stopped(self) -> bool:
        return self.state == RobotState.EMERGENCY_STOPPED
