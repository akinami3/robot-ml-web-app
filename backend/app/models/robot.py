"""
Database models for robot-related data
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class RobotStatus(Base):
    """Robot status model"""

    __tablename__ = "robot_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Position
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)

    # Orientation (quaternion)
    orientation_x = Column(Float, nullable=True)
    orientation_y = Column(Float, nullable=True)
    orientation_z = Column(Float, nullable=True)
    orientation_w = Column(Float, nullable=True)

    # Velocity
    velocity_x = Column(Float, nullable=True)
    velocity_y = Column(Float, nullable=True)
    velocity_z = Column(Float, nullable=True)
    angular_velocity = Column(Float, nullable=True)

    # System status
    battery_level = Column(Float, nullable=True)
    connection_status = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Additional status data (JSON)
    extra_data = Column(JSON, nullable=True)


class RobotCommand(Base):
    """Robot command history"""

    __tablename__ = "robot_commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    command_type = Column(String(50), nullable=False)  # velocity, navigation, etc.

    # Velocity command
    velocity_x = Column(Float, nullable=True)
    velocity_y = Column(Float, nullable=True)
    velocity_z = Column(Float, nullable=True)
    angular_velocity = Column(Float, nullable=True)

    # Command data (JSON)
    command_data = Column(JSON, nullable=True)
    status = Column(String(20), nullable=True)  # sent, acknowledged, failed


class NavigationGoal(Base):
    """Navigation goal model"""

    __tablename__ = "navigation_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_name = Column(String(100), nullable=True)

    # Goal position
    target_x = Column(Float, nullable=False)
    target_y = Column(Float, nullable=False)
    target_z = Column(Float, nullable=True, default=0.0)

    # Target orientation (quaternion)
    orientation_x = Column(Float, nullable=True)
    orientation_y = Column(Float, nullable=True)
    orientation_z = Column(Float, nullable=True)
    orientation_w = Column(Float, nullable=True)

    # Navigation status
    status = Column(String(20), nullable=False, default="pending")  # pending, active, completed, failed, cancelled
    progress = Column(Float, nullable=True)  # 0.0 to 1.0
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
