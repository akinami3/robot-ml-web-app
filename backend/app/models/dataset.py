"""
Database models for dataset and recording
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class RecordingSession(Base):
    """Recording session model"""

    __tablename__ = "recording_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status: recording, paused, completed, discarded
    status = Column(String(20), nullable=False, default="recording", index=True)

    # Selected data types to record
    selected_data_types = Column(ARRAY(String), nullable=False)

    # Timing
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    pause_time = Column(DateTime, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Relationships
    data_points = relationship("RobotDataPoint", back_populates="session", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="session")


class RobotDataPoint(Base):
    """Individual robot data point"""

    __tablename__ = "robot_data_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("recording_sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Velocity
    velocity_x = Column(Float, nullable=True)
    velocity_y = Column(Float, nullable=True)
    velocity_z = Column(Float, nullable=True)
    angular_velocity = Column(Float, nullable=True)

    # Position
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)

    # Orientation (quaternion)
    orientation_x = Column(Float, nullable=True)
    orientation_y = Column(Float, nullable=True)
    orientation_z = Column(Float, nullable=True)
    orientation_w = Column(Float, nullable=True)

    # System status
    battery_level = Column(Float, nullable=True)

    # Camera image path (stored in file system)
    camera_image_path = Column(String(500), nullable=True)

    # Additional status data (JSON)
    status_json = Column(JSON, nullable=True)

    # Relationships
    session = relationship("RecordingSession", back_populates="data_points")


class Dataset(Base):
    """Dataset model created from recording sessions"""

    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("recording_sessions.id"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Selected data types included in this dataset
    data_types = Column(ARRAY(String), nullable=False)

    # Dataset statistics
    total_samples = Column(Integer, nullable=False, default=0)
    train_samples = Column(Integer, nullable=True)
    val_samples = Column(Integer, nullable=True)
    test_samples = Column(Integer, nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)

    # Relationships
    session = relationship("RecordingSession", back_populates="datasets")
    ml_models = relationship("MLModel", back_populates="dataset")
