"""
Chat repositories
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatConversation, ChatMessage
from app.repositories.base import BaseRepository


class ChatConversationRepository(BaseRepository[ChatConversation]):
    """Repository for chat conversations"""

    def __init__(self):
        super().__init__(ChatConversation)

    async def get_with_messages(
        self, db: AsyncSession, id: UUID
    ) -> Optional[ChatConversation]:
        """Get conversation with all messages"""
        result = await db.execute(
            select(ChatConversation)
            .options(selectinload(ChatConversation.messages))
            .where(ChatConversation.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_session(
        self, db: AsyncSession, session_id: str
    ) -> Optional[ChatConversation]:
        """Get conversation by session ID"""
        result = await db.execute(
            select(ChatConversation)
            .options(selectinload(ChatConversation.messages))
            .where(ChatConversation.session_id == session_id)
        )
        return result.scalar_one_or_none()


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for chat messages"""

    def __init__(self):
        super().__init__(ChatMessage)

    async def get_by_conversation(
        self, db: AsyncSession, conversation_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        """Get messages for a conversation"""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.timestamp.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


# Global instances
chat_conversation_repo = ChatConversationRepository()
chat_message_repo = ChatMessageRepository()
