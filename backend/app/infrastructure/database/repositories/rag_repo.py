"""SQLAlchemy implementation of RAGRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.rag_document import DocumentChunk, RAGDocument
from ....domain.repositories.rag_repository import RAGRepository
from ..models import DocumentChunkModel, RAGDocumentModel


class SQLAlchemyRAGRepository(RAGRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _doc_to_entity(self, model: RAGDocumentModel) -> RAGDocument:
        return RAGDocument(
            id=model.id,
            title=model.title,
            content=model.content,
            source=model.source,
            owner_id=model.owner_id,
            file_type=model.file_type,
            file_size=model.file_size,
            chunk_count=model.chunk_count,
            metadata=model.metadata_ or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _chunk_to_entity(self, model: DocumentChunkModel) -> DocumentChunk:
        emb = list(model.embedding) if model.embedding is not None else []
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            content=model.content,
            embedding=emb,
            chunk_index=model.chunk_index,
            token_count=model.token_count,
            metadata=model.metadata_ or {},
            created_at=model.created_at,
        )

    async def get_by_id(self, id: UUID) -> RAGDocument | None:
        result = await self._session.get(RAGDocumentModel, id)
        return self._doc_to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[RAGDocument]:
        stmt = select(RAGDocumentModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._doc_to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: RAGDocument) -> RAGDocument:
        model = RAGDocumentModel(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            source=entity.source,
            owner_id=entity.owner_id,
            file_type=entity.file_type,
            file_size=entity.file_size,
            chunk_count=entity.chunk_count,
            metadata_=entity.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return self._doc_to_entity(model)

    async def update(self, entity: RAGDocument) -> RAGDocument:
        model = await self._session.get(RAGDocumentModel, entity.id)
        if model is None:
            raise ValueError(f"Document {entity.id} not found")
        model.title = entity.title
        model.metadata_ = entity.metadata
        await self._session.flush()
        return self._doc_to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(RAGDocumentModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(RAGDocumentModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_owner(self, owner_id: UUID) -> list[RAGDocument]:
        stmt = (
            select(RAGDocumentModel)
            .where(RAGDocumentModel.owner_id == owner_id)
            .order_by(RAGDocumentModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._doc_to_entity(m) for m in result.scalars().all()]

    async def create_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        model = DocumentChunkModel(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            embedding=chunk.embedding if chunk.embedding else None,
            chunk_index=chunk.chunk_index,
            token_count=chunk.token_count,
            metadata_=chunk.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return self._chunk_to_entity(model)

    async def create_chunks_bulk(self, chunks: list[DocumentChunk]) -> int:
        models = [
            DocumentChunkModel(
                id=c.id,
                document_id=c.document_id,
                content=c.content,
                embedding=c.embedding if c.embedding else None,
                chunk_index=c.chunk_index,
                token_count=c.token_count,
                metadata_=c.metadata,
            )
            for c in chunks
        ]
        self._session.add_all(models)
        await self._session.flush()
        return len(models)

    async def get_chunks_by_document(
        self, document_id: UUID
    ) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index.asc())
        )
        result = await self._session.execute(stmt)
        return [self._chunk_to_entity(m) for m in result.scalars().all()]

    async def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[DocumentChunk, float]]:
        """Use pgvector cosine similarity search."""
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        stmt = text(
            """
            SELECT *,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM document_chunks
            WHERE embedding IS NOT NULL
              AND 1 - (embedding <=> :embedding::vector) >= :min_similarity
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "embedding": embedding_str,
                "min_similarity": min_similarity,
                "limit": limit,
            },
        )
        rows = result.fetchall()
        chunks_with_similarity = []
        for row in rows:
            chunk = DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                embedding=[],  # don't load full embedding
                chunk_index=row.chunk_index,
                token_count=row.token_count,
                metadata=row.metadata_ if hasattr(row, "metadata_") else {},
                created_at=row.created_at,
            )
            chunks_with_similarity.append((chunk, float(row.similarity)))
        return chunks_with_similarity

    async def delete_chunks_by_document(self, document_id: UUID) -> int:
        stmt = delete(DocumentChunkModel).where(
            DocumentChunkModel.document_id == document_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount
