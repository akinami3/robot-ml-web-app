"""
Sensor Data Model - for ML data recording
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Index
from sqlalchemy.sql import func

from app.models.models import Base


class SensorDataRecord(Base):
    """Sensor/Control data recorded from robots for ML training"""
    __tablename__ = "sensor_data_records"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String(50), index=True, nullable=False)
    
    # Timestamp from gateway (milliseconds)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    
    # Sensor values (e.g., lidar distances, IMU accel/gyro, encoders)
    sensor_data = Column(JSON, nullable=False, default={})
    
    # Control values (e.g., linear_velocity, angular_velocity, steering)
    control_data = Column(JSON, nullable=False, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_sensor_data_robot_time', 'robot_id', 'recorded_at'),
    )
