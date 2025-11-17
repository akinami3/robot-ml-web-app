from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

from app.infrastructure.database.models.chat_document import ChatDocumentModel


@dataclass
class RetrievedDocument:
    id: str
    title: str
    content: str
    score: float


class Retriever:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search(self, query: str, limit: int = 3) -> Sequence[RetrievedDocument]:
        documents: Iterable[ChatDocumentModel] = (
            self._db.query(ChatDocumentModel)
            .order_by(ChatDocumentModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            RetrievedDocument(
                id=str(doc.id),
                title=doc.title,
                content=doc.content,
                score=1.0,
            )
            for doc in documents
        ]
