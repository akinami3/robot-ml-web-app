"""Pydantic schemas for API request/response."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ─── Auth ────────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "viewer"


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None


# ─── Robots ──────────────────────────────────────────────────────────────────


class RobotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    adapter_type: str
    connection_params: dict[str, Any] = Field(default_factory=dict)


class RobotResponse(BaseModel):
    id: UUID
    name: str
    adapter_type: str
    state: str
    capabilities: list[str]
    battery_level: float | None = None
    last_seen: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RobotUpdate(BaseModel):
    name: str | None = None
    connection_params: dict[str, Any] | None = None


# ─── Sensor Data ─────────────────────────────────────────────────────────────


class SensorDataResponse(BaseModel):
    id: UUID
    robot_id: UUID
    sensor_type: str
    data: dict[str, Any]
    timestamp: datetime
    session_id: UUID | None = None
    sequence_number: int = 0

    model_config = {"from_attributes": True}


class SensorDataQuery(BaseModel):
    robot_id: UUID
    sensor_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = Field(default=100, ge=1, le=10000)


class AggregatedDataQuery(BaseModel):
    robot_id: UUID
    sensor_type: str
    start_time: datetime
    end_time: datetime
    bucket_seconds: int = Field(default=60, ge=1, le=86400)


# ─── Datasets ────────────────────────────────────────────────────────────────


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    robot_ids: list[UUID]
    sensor_types: list[str]
    start_time: datetime | None = None
    end_time: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    description: str
    owner_id: UUID
    status: str
    sensor_types: list[str]
    robot_ids: list[UUID]
    start_time: datetime | None = None
    end_time: datetime | None = None
    record_count: int
    size_bytes: int
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetExportRequest(BaseModel):
    format: str = "csv"  # csv, parquet, json


# ─── Recording ───────────────────────────────────────────────────────────────


class RecordingStartRequest(BaseModel):
    robot_id: UUID
    sensor_types: list[str] = Field(default_factory=list)
    max_frequency_hz: dict[str, float] = Field(default_factory=dict)


class RecordingResponse(BaseModel):
    id: UUID
    robot_id: UUID
    user_id: UUID
    is_active: bool
    record_count: int
    size_bytes: int
    started_at: datetime
    stopped_at: datetime | None = None
    config: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}


# ─── RAG ─────────────────────────────────────────────────────────────────────


class RAGDocumentResponse(BaseModel):
    id: UUID
    title: str
    source: str
    file_type: str
    file_size: int
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    context_used: bool


# ─── Audit ───────────────────────────────────────────────────────────────────


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: str
    details: dict
    ip_address: str
    timestamp: datetime

    model_config = {"from_attributes": True}


# ─── Common ──────────────────────────────────────────────────────────────────


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    offset: int
    limit: int


class ErrorResponse(BaseModel):
    detail: str
    code: str = ""
