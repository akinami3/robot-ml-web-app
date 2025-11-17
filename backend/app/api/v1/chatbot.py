from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.chatbot import ChatQuery, ChatResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


def get_service(db: Session = Depends(get_db)) -> ChatbotService:
    return ChatbotService(db)


@router.post("/query", response_model=ChatResponse)
async def query(
    payload: ChatQuery,
    service: ChatbotService = Depends(get_service),
) -> ChatResponse:
    return await service.ask(payload)
