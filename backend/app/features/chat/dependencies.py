"""Dependency wiring for the chat feature."""

from __future__ import annotations

from fastapi import Depends, Request

from app.application.interfaces import UnitOfWork
from app.core.base_dependencies import (
    get_unit_of_work,
    get_llm_client,
    get_vector_store,
    get_websocket_hub,
)
from app.repositories.rag_documents import RAGDocumentRepository
from .service import ChatbotService


__all__ = ["get_chatbot_service"]


async def get_chatbot_service(
    request: Request,
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> ChatbotService:
    return ChatbotService(
        unit_of_work=unit_of_work,
        rag_repo=RAGDocumentRepository(unit_of_work.session),
        vector_store=get_vector_store(request),
        llm_client=get_llm_client(request),
        websocket_hub=get_websocket_hub(request),
    )
