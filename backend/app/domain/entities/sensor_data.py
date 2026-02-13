"""Sensor data domain entity."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class SensorType(str, enum.Enum):
    LIDAR = "lidar"
    CAMERA = "camera"
    IMU = "imu"
    ODOMETRY = "odometry"
    BATTERY = "battery"
    GPS = "gps"
    POINT_CLOUD = "point_cloud"
    JOINT_STATE = "joint_state"


@dataclass
class SensorData:
    robot_id: UUID
    sensor_type: SensorType
    data: dict[str, Any]
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: UUID | None = None
    sequence_number: int = 0

    @property
    def is_image_type(self) -> bool:
        return self.sensor_type == SensorType.CAMERA

    @property
    def is_time_series(self) -> bool:
        return self.sensor_type in (
            SensorType.IMU,
            SensorType.ODOMETRY,
            SensorType.BATTERY,
            SensorType.GPS,
        )
