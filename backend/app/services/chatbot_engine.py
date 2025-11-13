"""Chatbot service combining RAG and LLM inference."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm_client import LLMClientAdapter
from app.adapters.vector_store import VectorStoreAdapter
from app.repositories.rag_documents import RAGDocumentRepository
from app.websocket.manager import WebSocketHub


@dataclass(slots=True)
class ChatQueryPayload:
    question: str
    robot_id: str | None = None
    top_k: int = 3


class ChatbotService:
    """RAG powered chatbot service."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        rag_repo: RAGDocumentRepository,
        vector_store: VectorStoreAdapter,
        llm_client: LLMClientAdapter,
        websocket_hub: WebSocketHub,
    ) -> None:
        self._session = session
        self._rag_repo = rag_repo
        self._vector_store = vector_store
        self._llm_client = llm_client
        self._ws_hub = websocket_hub

    async def query(self, payload: ChatQueryPayload) -> dict:
        documents = await self._vector_store.similarity_search(
            query=payload.question, top_k=payload.top_k
        )
        formatted_context = "\n\n".join(
            f"Source: {doc['source']}\n{doc['content']}" for doc in documents
        )
        response = await self._llm_client.generate(
            prompt=f"Context:\n{formatted_context}\n\nQuestion: {payload.question}\nAnswer:"
        )

        message = {
            "question": payload.question,
            "answer": response,
            "documents": documents,
        }
        await self._ws_hub.broadcast(channel="chat", message=message)
        await self._session.commit()
        return message
