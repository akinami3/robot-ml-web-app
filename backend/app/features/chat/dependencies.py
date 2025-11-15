"""Dependency wiring for the chat feature."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_dependencies import (
    get_db_session,
    get_llm_client,
    get_vector_store,
    get_websocket_hub,
)
from app.repositories.rag_documents import RAGDocumentRepository
from .service import ChatbotService


__all__ = ["get_chatbot_service"]


async def get_chatbot_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ChatbotService:
    return ChatbotService(
        rag_repo=RAGDocumentRepository(session),
        vector_store=get_vector_store(request),
        llm_client=get_llm_client(request),
        websocket_hub=get_websocket_hub(request),
    )
