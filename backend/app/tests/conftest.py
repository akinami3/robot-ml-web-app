"""Pytest fixtures for API tests."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_robot_control_service
from app.main import app
from app.services.robot_control import NavigationGoalPayload, VelocityCommandPayload


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    original_overrides = app.dependency_overrides.copy()

    class StubRobotControlService:
        def __init__(self) -> None:
            self.velocity_payloads: list[VelocityCommandPayload] = []
            self.navigation_payloads: list[NavigationGoalPayload] = []

        async def set_velocity(self, payload: VelocityCommandPayload) -> None:
            self.velocity_payloads.append(payload)

        async def send_navigation_goal(self, payload: NavigationGoalPayload) -> None:
            self.navigation_payloads.append(payload)

        async def toggle_session_recording(self, *, robot_id: str, enable: bool, metadata: dict | None = None) -> None:
            return None

    stub_service = StubRobotControlService()
    app.dependency_overrides[get_robot_control_service] = lambda: stub_service

    transport = ASGITransport(app=app, lifespan="off")
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        setattr(test_client, "stub_robot_service", stub_service)
        yield test_client

    app.dependency_overrides = original_overrides
