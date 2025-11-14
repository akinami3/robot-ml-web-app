"""Chat feature HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_chatbot_service
from app.features.chat.schemas import ChatQueryRequest, ChatResponse
from app.features.chat.service import ChatQueryPayload, ChatbotService

router = APIRouter()


@router.post("/query", response_model=ChatResponse)
async def chat(
    request: ChatQueryRequest,
    service: ChatbotService = Depends(get_chatbot_service),
) -> ChatResponse:
    payload = ChatQueryPayload(
        question=request.question,
        robot_id=request.robot_id,
        top_k=request.top_k,
    )
    result = await service.query(payload)
    return ChatResponse(**result)
