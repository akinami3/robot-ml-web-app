"""RAG document domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class RAGDocument:
    title: str
    content: str
    source: str
    owner_id: UUID
    id: UUID = field(default_factory=uuid4)
    file_type: str = "text"
    file_size: int = 0
    chunk_count: int = 0
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentChunk:
    document_id: UUID
    content: str
    embedding: list[float] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)
    chunk_index: int = 0
    token_count: int = 0
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
