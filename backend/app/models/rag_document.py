"""RAG document model for chatbot context."""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base, TimestampMixin


class RAGDocument(Base, TimestampMixin):
    """Document stored for retrieval augmented generation."""

    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source: Mapped[str] = mapped_column(String(length=128), nullable=False)
    title: Mapped[str] = mapped_column(String(length=256), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
