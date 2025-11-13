"""Repository for RAG documents used by the chatbot."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RAGDocument
from app.repositories.base import BaseRepository


class RAGDocumentRepository(BaseRepository):
    """Persist and retrieve documents for retrieval augmented generation."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add_document(
        self,
        *,
        source: str,
        title: str,
        content: str,
        metadata: dict | None = None,
    ) -> RAGDocument:
        document = RAGDocument(
            source=source,
            title=title,
            content=content,
            metadata=metadata,
        )
        return await self.add(document)

    async def list_documents(self) -> list[RAGDocument]:
        result = await self.session.execute(select(RAGDocument))
        return list(result.scalars().all())
