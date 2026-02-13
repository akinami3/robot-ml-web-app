"""SQLAlchemy ORM models with TimescaleDB and pgvector support."""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...domain.entities.audit_log import AuditAction
from ...domain.entities.dataset import DatasetStatus
from ...domain.entities.robot import RobotState
from ...domain.entities.sensor_data import SensorType
from ...domain.entities.user import UserRole
from .connection import Base


# ─── Users ───────────────────────────────────────────────────────────────────


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    datasets = relationship("DatasetModel", back_populates="owner", lazy="selectin")
    audit_logs = relationship("AuditLogModel", back_populates="user", lazy="noload")


# ─── Robots ──────────────────────────────────────────────────────────────────


class RobotModel(Base):
    __tablename__ = "robots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    adapter_type: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(
        Enum(RobotState, name="robot_state", create_constraint=True),
        default=RobotState.DISCONNECTED,
    )
    capabilities: Mapped[list] = mapped_column(ARRAY(String), default=[])
    connection_params: Mapped[dict] = mapped_column(JSONB, default={})
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_robots_state", "state"),)


# ─── Sensor Data (TimescaleDB Hypertable) ───────────────────────────────────


class SensorDataModel(Base):
    __tablename__ = "sensor_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    sensor_type: Mapped[str] = mapped_column(
        Enum(SensorType, name="sensor_type", create_constraint=True), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("ix_sensor_data_robot_type_time", "robot_id", "sensor_type", "timestamp"),
        # TimescaleDB hypertable will be created via migration
        {"timescaledb_hypertable": {"time_column_name": "timestamp"}},
    )


# ─── Datasets ────────────────────────────────────────────────────────────────


class DatasetModel(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(DatasetStatus, name="dataset_status", create_constraint=True),
        default=DatasetStatus.CREATING,
    )
    sensor_types: Mapped[list] = mapped_column(ARRAY(String), default=[])
    robot_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=[])
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=[])
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("UserModel", back_populates="datasets")

    __table_args__ = (
        Index("ix_datasets_owner", "owner_id"),
        Index("ix_datasets_status", "status"),
    )


# ─── RAG Documents ───────────────────────────────────────────────────────────


class RAGDocumentModel(Base):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(1000), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_type: Mapped[str] = mapped_column(String(50), default="text")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks = relationship(
        "DocumentChunkModel", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_rag_documents_owner", "owner_id"),)


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=True)  # nomic-embed-text dim
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document = relationship("RAGDocumentModel", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunks_document", "document_id"),
        # HNSW index for pgvector similarity search
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


# ─── Recording Sessions ──────────────────────────────────────────────────────


class RecordingSessionModel(Base):
    __tablename__ = "recording_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True
    )

    __table_args__ = (
        Index("ix_recording_sessions_active", "robot_id", "is_active"),
    )


# ─── Audit Logs ──────────────────────────────────────────────────────────────


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        Enum(AuditAction, name="audit_action", create_constraint=True), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(100), default="")
    resource_id: Mapped[str] = mapped_column(String(255), default="")
    details: Mapped[dict] = mapped_column(JSONB, default={})
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user = relationship("UserModel", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_time", "user_id", "timestamp"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
