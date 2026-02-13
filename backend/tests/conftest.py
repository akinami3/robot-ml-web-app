"""Test configuration and fixtures."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.core.security import hash_password
from app.domain.entities.user import User, UserRole
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        debug=True,
        database_url="sqlite+aiosqlite:///test.db",
        redis_url="redis://localhost:6379/1",
        secret_key="test-secret-key",
        jwt_algorithm="HS256",
        cors_origins="http://localhost:3000",
    )


@pytest.fixture
def test_user() -> User:
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.OPERATOR,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def admin_user() -> User:
    return User(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
