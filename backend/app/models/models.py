"""
Database Models - SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class RobotState(str, enum.Enum):
    """Robot state enum"""
    IDLE = "IDLE"
    MOVING = "MOVING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    CHARGING = "CHARGING"


class UserRole(str, enum.Enum):
    """User role enum"""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    missions = relationship("Mission", back_populates="created_by_user")


class Robot(Base):
    """Robot model"""
    __tablename__ = "robots"
    
    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    vendor = Column(String(100), nullable=False)
    model = Column(String(100))
    
    # Current state
    state = Column(Enum(RobotState), default=RobotState.IDLE)
    battery = Column(Float, default=100.0)
    
    # Position
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    pos_theta = Column(Float, default=0.0)
    
    # Capabilities
    capabilities = Column(JSON, default={})
    
    # Metadata
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    missions = relationship("Mission", back_populates="robot")
    logs = relationship("RobotLog", back_populates="robot")


class Mission(Base):
    """Mission model"""
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    
    # Mission details
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Goal position
    goal_x = Column(Float, nullable=False)
    goal_y = Column(Float, nullable=False)
    goal_theta = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    robot = relationship("Robot", back_populates="missions")
    created_by_user = relationship("User", back_populates="missions")


class RobotLog(Base):
    """Robot log model"""
    __tablename__ = "robot_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=False)
    
    # Log data
    log_type = Column(String(50), nullable=False)  # STATE_CHANGE, ERROR, INFO, SENSOR
    message = Column(String(1000))
    data = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    robot = relationship("Robot", back_populates="logs")
