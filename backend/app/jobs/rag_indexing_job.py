"""Job for indexing documents into the vector store."""

from __future__ import annotations

import asyncio
import structlog

from app.adapters.vector_store import VectorStoreAdapter

logger = structlog.get_logger(__name__)


async def index_document(document_id: str, embedding: list[float], payload: dict) -> None:
    adapter = VectorStoreAdapter()
    await adapter.index_document(document_id=document_id, embedding=embedding, payload=payload)
    await asyncio.sleep(0)
    logger.info("jobs.rag_indexed", document_id=document_id)
