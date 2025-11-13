"""Service that processes incoming telemetry messages."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionInactiveError
from app.repositories.sensor_data import SensorDataRepository
from app.services.datalogger import DataLoggerService
from app.websocket.manager import WebSocketHub


class TelemetryProcessorService:
    """Handles streaming telemetry and conditional persistence."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        datalogger: DataLoggerService,
        sensor_repo: SensorDataRepository,
        websocket_hub: WebSocketHub,
    ) -> None:
        self._session = session
        self._datalogger = datalogger
        self._sensor_repo = sensor_repo
        self._ws_hub = websocket_hub

    async def handle_mqtt_message(
        self,
        *,
        robot_id: str,
        sensor_type: str,
        payload: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None:
        try:
            await self._datalogger.save_sensor_payload(
                robot_id=robot_id,
                sensor_type=sensor_type,
                payload=payload,
                latitude=latitude,
                longitude=longitude,
            )
        except SessionInactiveError:
            # Recording is off; ignore persistence but still broadcast to UI
            pass
        else:
            await self._session.commit()

        await self._ws_hub.broadcast(
            channel="telemetry",
            message={
                "robot_id": robot_id,
                "sensor_type": sensor_type,
                "payload": payload,
            },
        )
