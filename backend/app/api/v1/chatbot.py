"""
Chatbot API endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.repositories.chat import ChatConversationRepository
from app.schemas.chatbot import (
    ChatConversationResponse,
    ChatMessage,
    ChatMessageCreate,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
)
from app.services.chatbot.chatbot_service import get_chatbot_service

router = APIRouter()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: Optional[ConversationCreate] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create new conversation"""
    chatbot_service = get_chatbot_service()
    title = conversation.title if conversation else None
    return await chatbot_service.create_conversation(db, title)


@router.post("/conversations/{conversation_id}/message", response_model=ChatMessage)
async def send_message(
    conversation_id: UUID,
    message: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Send message to chatbot and get response
    
    Uses RAG (Retrieval-Augmented Generation) to provide context-aware answers
    """
    chatbot_service = get_chatbot_service()
    return await chatbot_service.send_message(db, conversation_id, message)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List chat conversation history"""
    conv_repo = ChatConversationRepository(db)
    conversations = await conv_repo.get_multi(skip=skip, limit=limit)
    
    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation message history"""
    chatbot_service = get_chatbot_service()
    return await chatbot_service.get_conversation_history(db, conversation_id)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete conversation"""
    chatbot_service = get_chatbot_service()
    return await chatbot_service.delete_conversation(db, conversation_id)
