"""Chat feature schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    robot_id: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class ChatResponse(BaseModel):
    question: str
    answer: str
    documents: list[dict[str, Any]]
