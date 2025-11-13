"""Telemetry endpoint tests."""

from __future__ import annotations

import pytest

from app.core.dependencies import get_datalogger_service
from app.main import app


@pytest.mark.asyncio
async def test_ingest_telemetry_accepts_payload(client):
    class StubDataLogger:
        async def start_session(self, **kwargs):
            return None

        async def save_sensor_payload(self, **kwargs):
            return None

        async def end_session(self, **kwargs):
            return None

    stub = StubDataLogger()
    app.dependency_overrides[get_datalogger_service] = lambda: stub

    response = await client.post(
        "/api/datalogger/telemetry",
        json={
            "robot_id": "robot-1",
            "sensor_type": "imu",
            "payload": {"ax": 1.0},
        },
    )

    app.dependency_overrides.pop(get_datalogger_service, None)

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
