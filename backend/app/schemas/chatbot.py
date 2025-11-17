"""
Pydantic schemas for chatbot
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Chat Message Schemas
class ChatMessageCreate(BaseModel):
    """Create chat message"""

    content: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    """Chat message response"""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    timestamp: datetime
    metadata: Optional[dict]

    class Config:
        from_attributes = True


# Chat Conversation Schemas
class ChatConversationResponse(BaseModel):
    """Chat conversation response"""

    id: UUID
    session_id: str
    title: Optional[str]
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


# Chat Response
class ChatResponse(BaseModel):
    """Chatbot response"""

    message: ChatMessageResponse
    sources: Optional[List[str]] = None
