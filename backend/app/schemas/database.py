"""
Pydantic schemas for database/recording
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Recording Session Schemas
class RecordingSessionCreate(BaseModel):
    """Create recording session"""

    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    selected_data_types: List[str] = Field(
        ..., description="Data types to record (velocity, position, camera, battery, etc.)"
    )


class RecordingSessionUpdate(BaseModel):
    """Update recording session"""

    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class RecordingSessionResponse(BaseModel):
    """Recording session response"""

    id: UUID
    name: str
    description: Optional[str]
    status: str
    selected_data_types: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    pause_time: Optional[datetime]
    created_at: datetime
    metadata: Optional[dict]

    class Config:
        from_attributes = True


# Dataset Schemas
class DatasetCreate(BaseModel):
    """Create dataset"""

    session_id: UUID
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    data_types: List[str]
    train_split: float = Field(0.7, ge=0.0, le=1.0)
    val_split: float = Field(0.2, ge=0.0, le=1.0)
    test_split: float = Field(0.1, ge=0.0, le=1.0)


class DatasetResponse(BaseModel):
    """Dataset response"""

    id: UUID
    session_id: UUID
    name: str
    description: Optional[str]
    data_types: List[str]
    total_samples: int
    train_samples: Optional[int]
    val_samples: Optional[int]
    test_samples: Optional[int]
    created_at: datetime
    metadata: Optional[dict]

    class Config:
        from_attributes = True


# Recording Control Schemas
class RecordingControlResponse(BaseModel):
    """Recording control response"""

    session_id: UUID
    status: str
    message: str
