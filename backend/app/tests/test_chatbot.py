"""Chatbot API tests."""

from __future__ import annotations

import pytest

from app.core.dependencies import get_chatbot_service
from app.main import app


@pytest.mark.asyncio
async def test_chat_query_returns_answer(client):
    class StubChatbot:
        async def query(self, payload):
            return {"question": payload.question, "answer": "Hello", "documents": []}

    stub = StubChatbot()
    app.dependency_overrides[get_chatbot_service] = lambda: stub

    response = await client.post(
        "/api/chat/query",
        json={"question": "Hi?"},
    )

    app.dependency_overrides.pop(get_chatbot_service, None)

    assert response.status_code == 200
    assert response.json()["answer"] == "Hello"
