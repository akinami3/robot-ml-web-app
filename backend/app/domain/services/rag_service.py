"""RAG service - domain logic for retrieval-augmented generation."""

from __future__ import annotations

import structlog
from typing import Any, Protocol
from uuid import UUID

from ..entities.rag_document import DocumentChunk, RAGDocument
from ..repositories.rag_repository import RAGRepository

logger = structlog.get_logger()


class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


class LLMProvider(Protocol):
    async def generate(self, prompt: str, context: str = "") -> str:
        ...

    async def generate_stream(self, prompt: str, context: str = ""):
        ...


class TextSplitter:
    """Simple text chunker."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            # try to break at sentence/paragraph boundary
            if end < len(text):
                for sep in ["\n\n", "\n", ". ", " "]:
                    last_sep = text[start:end].rfind(sep)
                    if last_sep > self.chunk_size // 2:
                        end = start + last_sep + len(sep)
                        break
            chunks.append(text[start:end].strip())
            start = end - self.overlap

        return [c for c in chunks if c]


class RAGService:
    def __init__(
        self,
        rag_repo: RAGRepository,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> None:
        self._repo = rag_repo
        self._embedder = embedding_provider
        self._llm = llm_provider
        self._splitter = TextSplitter(chunk_size, chunk_overlap)

    async def ingest_document(
        self,
        title: str,
        content: str,
        source: str,
        owner_id: UUID,
        file_type: str = "text",
        file_size: int = 0,
        metadata: dict | None = None,
    ) -> RAGDocument:
        # Split into chunks
        chunk_texts = self._splitter.split(content)

        # Embed chunks
        embeddings = await self._embedder.embed_batch(chunk_texts)

        # Create document
        doc = RAGDocument(
            title=title,
            content=content[:1000],  # store preview
            source=source,
            owner_id=owner_id,
            file_type=file_type,
            file_size=file_size,
            chunk_count=len(chunk_texts),
            metadata=metadata or {},
        )
        created_doc = await self._repo.create(doc)

        # Create chunks with embeddings
        chunks = [
            DocumentChunk(
                document_id=created_doc.id,
                content=text,
                embedding=emb,
                chunk_index=i,
                token_count=len(text.split()),
            )
            for i, (text, emb) in enumerate(zip(chunk_texts, embeddings))
        ]
        await self._repo.create_chunks_bulk(chunks)

        logger.info(
            "document_ingested",
            doc_id=str(created_doc.id),
            title=title,
            chunks=len(chunks),
        )
        return created_doc

    async def query(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> dict[str, Any]:
        # Embed question
        query_embedding = await self._embedder.embed(question)

        # Find similar chunks
        results = await self._repo.search_similar_chunks(
            embedding=query_embedding,
            limit=top_k,
            min_similarity=min_similarity,
        )

        if not results:
            answer = await self._llm.generate(question)
            return {
                "answer": answer,
                "sources": [],
                "context_used": False,
            }

        # Build context
        context_parts = []
        sources = []
        for chunk, similarity in results:
            context_parts.append(chunk.content)
            sources.append(
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "similarity": similarity,
                    "preview": chunk.content[:200],
                }
            )

        context = "\n\n---\n\n".join(context_parts)

        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        answer = await self._llm.generate(prompt, context)

        return {
            "answer": answer,
            "sources": sources,
            "context_used": True,
        }

    async def query_stream(
        self,
        question: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ):
        """Streaming version of query."""
        query_embedding = await self._embedder.embed(question)
        results = await self._repo.search_similar_chunks(
            embedding=query_embedding,
            limit=top_k,
            min_similarity=min_similarity,
        )

        context = ""
        if results:
            context_parts = [chunk.content for chunk, _ in results]
            context = "\n\n---\n\n".join(context_parts)

        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        ) if context else question

        async for token in self._llm.generate_stream(prompt, context):
            yield token

    async def delete_document(self, doc_id: UUID) -> bool:
        await self._repo.delete_chunks_by_document(doc_id)
        return await self._repo.delete(doc_id)

    async def list_documents(self, owner_id: UUID) -> list[RAGDocument]:
        return await self._repo.get_by_owner(owner_id)
