"""
Pydantic schemas for machine learning
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ML Model Schemas
class MLModelCreate(BaseModel):
    """Create ML model"""

    dataset_id: UUID
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    model_type: str = Field(..., max_length=100)
    architecture: Optional[str] = None
    hyperparameters: Optional[Dict] = None
    total_epochs: int = Field(100, ge=1)


class MLModelResponse(BaseModel):
    """ML model response"""

    id: UUID
    dataset_id: UUID
    name: str
    description: Optional[str]
    model_type: str
    architecture: Optional[str]
    hyperparameters: Optional[Dict]
    training_status: str
    model_path: Optional[str]
    best_train_loss: Optional[float]
    best_val_loss: Optional[float]
    best_train_accuracy: Optional[float]
    best_val_accuracy: Optional[float]
    current_epoch: Optional[int]
    total_epochs: Optional[int]
    created_at: datetime
    training_started_at: Optional[datetime]
    training_completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Training Control Schemas
class TrainingStartRequest(BaseModel):
    """Start training request"""

    model_id: UUID
    resume: bool = False


class TrainingStopRequest(BaseModel):
    """Stop training request"""

    model_id: UUID
    save_checkpoint: bool = True


# Training Metrics Schemas
class TrainingMetrics(BaseModel):
    """Training metrics"""

    epoch: int
    train_loss: float
    val_loss: Optional[float]
    train_accuracy: Optional[float]
    val_accuracy: Optional[float]
    learning_rate: Optional[float]
    timestamp: datetime


class TrainingMetricsResponse(BaseModel):
    """Training metrics response"""

    model_id: UUID
    metrics: List[TrainingMetrics]


# Evaluation Schemas
class EvaluationResult(BaseModel):
    """Model evaluation result"""

    model_id: UUID
    test_loss: float
    test_accuracy: float
    additional_metrics: Optional[Dict]
    evaluated_at: datetime
