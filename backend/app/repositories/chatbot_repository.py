from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.infrastructure.database.models.chat_document import ChatDocumentModel


class ChatbotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_documents(self, limit: int = 20) -> Sequence[ChatDocumentModel]:
        return (
            self._db.query(ChatDocumentModel)
            .order_by(ChatDocumentModel.created_at.desc())
            .limit(limit)
            .all()
        )
