"""
Chatbot API endpoints
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.chatbot import (
    ChatConversationResponse,
    ChatMessageCreate,
    ChatResponse,
)

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(message: ChatMessageCreate, db: AsyncSession = Depends(get_db)):
    """
    Send message to chatbot and get response
    
    Uses RAG (Retrieval-Augmented Generation) to provide context-aware answers
    """
    # TODO: Implement RAG + LLM service
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/conversations", response_model=List[ChatConversationResponse])
async def list_conversations(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """List chat conversation history"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/conversations/{conversation_id}", response_model=ChatConversationResponse)
async def get_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get conversation details"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete conversation"""
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented yet")
