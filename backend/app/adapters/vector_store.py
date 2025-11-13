"""Vector store adapter for semantic search."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, PointStruct, VectorParams
except Exception:  # pragma: no cover - optional dependency fallback
    QdrantClient = None  # type: ignore

from app.core.config import settings

logger = structlog.get_logger(__name__)


class VectorStoreAdapter:
    """Provide async-friendly access to the vector database."""

    def __init__(self) -> None:
        self._collection_name = "robot_ml_docs"
        self._client: QdrantClient | None = None
        if settings.vector_store_url and QdrantClient:
            self._client = QdrantClient(url=settings.vector_store_url)
            self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self._client:
            return
        try:
            collections = self._client.get_collections()
            if self._collection_name not in {c.name for c in collections.collections}:
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(size=768, distance="Cosine"),
                )
        except Exception as exc:  # pragma: no cover - setup failure is non fatal
            logger.warning("vector_store.init_failed", error=str(exc))

    async def index_document(self, *, document_id: str, embedding: list[float], payload: dict[str, Any]) -> None:
        if not self._client:
            logger.info("vector_store.index.noop", document_id=document_id)
            return

        async def _write() -> None:
            assert self._client is not None
            point = PointStruct(id=document_id, vector=embedding, payload=payload)
            self._client.upsert(collection_name=self._collection_name, points=[point])

        await asyncio.to_thread(_write)

    async def similarity_search(self, *, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self._client:
            logger.info("vector_store.search.noop", query=query)
            return []

        async def _search() -> list[dict[str, Any]]:
            assert self._client is not None
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=[0.0] * 768,  # Replace with embedding model inference
                limit=top_k,
                query_filter=Filter(must=[]),
            )
            return [hit.payload for hit in results]

        return await asyncio.to_thread(_search)
