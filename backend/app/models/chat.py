"""
Database models for chatbot
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class ChatConversation(Base):
    """Chat conversation model"""

    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=True)

    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model"""

    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False, index=True)

    # Message role: user, assistant, system
    role = Column(String(20), nullable=False)

    # Message content
    content = Column(Text, nullable=False)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Metadata (sources, tokens, etc.)
    metadata = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
