"""RAG repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from ..entities.rag_document import DocumentChunk, RAGDocument
from .base import BaseRepository


class RAGRepository(BaseRepository[RAGDocument]):
    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> list[RAGDocument]:
        ...

    @abstractmethod
    async def create_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        ...

    @abstractmethod
    async def create_chunks_bulk(self, chunks: list[DocumentChunk]) -> int:
        ...

    @abstractmethod
    async def get_chunks_by_document(
        self, document_id: UUID
    ) -> list[DocumentChunk]:
        ...

    @abstractmethod
    async def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[DocumentChunk, float]]:
        ...

    @abstractmethod
    async def delete_chunks_by_document(self, document_id: UUID) -> int:
        ...
