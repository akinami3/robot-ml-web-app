"""Tests for ML pipeline endpoints."""

from __future__ import annotations

import uuid

import pytest

from app.core.dependencies import get_ml_pipeline_service
from app.main import app


@pytest.mark.asyncio
async def test_launch_training_enqueues_job(client):
    class StubMLService:
        async def launch_training(self, payload):
            return uuid.uuid4()

        async def get_run_metrics(self, run_id):
            return []

    stub = StubMLService()
    app.dependency_overrides[get_ml_pipeline_service] = lambda: stub

    response = await client.post(
        "/api/ml/train",
        json={
            "model_name": "resnet",
            "robot_id": "robot-1",
            "hyperparameters": {"lr": 0.001},
        },
    )

    app.dependency_overrides.pop(get_ml_pipeline_service, None)

    assert response.status_code == 200
    body = response.json()
    assert "run_id" in body
