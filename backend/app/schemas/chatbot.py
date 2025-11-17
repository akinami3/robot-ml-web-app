from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatQuery(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponseSource(BaseModel):
    id: str
    title: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatResponseSource]


class ChatMessage(BaseModel):
    id: UUID
    question: str
    answer: str
    created_at: datetime
