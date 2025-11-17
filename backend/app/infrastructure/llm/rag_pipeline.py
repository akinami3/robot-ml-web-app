from __future__ import annotations

import logging
from typing import Sequence

from app.infrastructure.llm.embeddings import EmbeddingProvider
from app.infrastructure.llm.retriever import RetrievedDocument

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self._embedding_provider = embedding_provider

    async def run(self, query: str, documents: Sequence[RetrievedDocument]) -> dict[str, object]:
        await self._embedding_provider.embed([query])
        answer = """現段階ではスタブ応答です。後ほど LLM 連携を実装してください。"""
        sources = [
            {
                "id": doc.id,
                "title": doc.title,
                "score": doc.score,
            }
            for doc in documents
        ]
        logger.debug("Generated RAG response for query='%s' sources=%d", query, len(sources))
        return {"answer": answer, "sources": sources}
