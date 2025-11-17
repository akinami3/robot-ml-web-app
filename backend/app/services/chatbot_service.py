from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.llm.embeddings import EmbeddingProvider
from app.infrastructure.llm.rag_pipeline import RAGPipeline
from app.infrastructure.llm.retriever import Retriever
from app.repositories.chatbot_repository import ChatbotRepository
from app.schemas.chatbot import ChatQuery, ChatResponse, ChatResponseSource

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = ChatbotRepository(db)
        settings = get_settings()
        embedding_provider = EmbeddingProvider(settings.embedding_model)
        self._pipeline = RAGPipeline(embedding_provider)

    async def ask(self, query: ChatQuery) -> ChatResponse:
        retriever = Retriever(self._db)
        documents = retriever.search(query.question)
        result = await self._pipeline.run(query.question, documents)
        sources = [ChatResponseSource(**source) for source in result["sources"]]
        return ChatResponse(answer=str(result["answer"]), sources=sources)
