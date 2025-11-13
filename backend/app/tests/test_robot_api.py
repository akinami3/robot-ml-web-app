"""Tests for robot API endpoints."""

from __future__ import annotations

import pytest

from app.schemas.robot import NavigationGoal, VelocityCommand


@pytest.mark.asyncio
async def test_set_velocity_accepts_request(client):
    payload = {"robot_id": "robot-1", "linear": 0.5, "angular": 0.1}
    response = await client.post("/api/robot/velocity", json=payload)
    assert response.status_code == 202
    stub = getattr(client, "stub_robot_service")
    assert stub.velocity_payloads[0].robot_id == "robot-1"


@pytest.mark.asyncio
async def test_send_navigation_goal(client):
    payload = {"robot_id": "robot-1", "target_x": 1.0, "target_y": 2.0, "orientation": 0.0}
    response = await client.post("/api/robot/navigation", json=payload)
    assert response.status_code == 202
    stub = getattr(client, "stub_robot_service")
    assert stub.navigation_payloads[0].target_x == 1.0
