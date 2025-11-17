"""
Database models for machine learning
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class MLModel(Base):
    """Machine learning model metadata"""

    __tablename__ = "ml_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Model configuration
    model_type = Column(String(100), nullable=False)  # e.g., CNN, LSTM, Transformer
    architecture = Column(Text, nullable=True)
    hyperparameters = Column(JSON, nullable=True)

    # Training status
    training_status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, running, paused, completed, failed

    # Model file path
    model_path = Column(String(500), nullable=True)
    checkpoint_path = Column(String(500), nullable=True)

    # Metrics
    best_train_loss = Column(Float, nullable=True)
    best_val_loss = Column(Float, nullable=True)
    best_train_accuracy = Column(Float, nullable=True)
    best_val_accuracy = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=True)  # Additional metrics

    # Training info
    current_epoch = Column(Integer, nullable=True, default=0)
    total_epochs = Column(Integer, nullable=True)
    training_started_at = Column(DateTime, nullable=True)
    training_completed_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="ml_models")
    training_history = relationship("TrainingHistory", back_populates="model", cascade="all, delete-orphan")


class TrainingHistory(Base):
    """Training history for each epoch"""

    __tablename__ = "training_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=False, index=True)

    epoch = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Loss metrics
    train_loss = Column(Float, nullable=False)
    val_loss = Column(Float, nullable=True)

    # Accuracy metrics
    train_accuracy = Column(Float, nullable=True)
    val_accuracy = Column(Float, nullable=True)

    # Learning rate
    learning_rate = Column(Float, nullable=True)

    # Additional metrics (JSON)
    additional_metrics = Column(JSON, nullable=True)

    # Relationships
    model = relationship("MLModel", back_populates="training_history")
