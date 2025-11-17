from sqlalchemy import Column, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.models.base import BaseModel, TimestampMixin


class ChatDocumentModel(TimestampMixin, BaseModel):
    __tablename__ = "chat_documents"

    source_id = Column(UUID(as_uuid=True), nullable=True)
    source_type = Column(String(length=64), nullable=False)
    title = Column(String(length=256), nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
