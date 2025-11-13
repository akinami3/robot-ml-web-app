"""Robot control service translating API requests to MQTT commands."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.mqtt_client import MQTTClientAdapter
from app.repositories.robot_state import RobotStateRepository
from app.services.datalogger import DataLoggerService
from app.websocket.manager import WebSocketHub


@dataclass
class VelocityCommandPayload:
    robot_id: str
    linear: float
    angular: float


@dataclass
class NavigationGoalPayload:
    robot_id: str
    target_x: float
    target_y: float
    orientation: float


class RobotControlService:
    """Business logic for robot actuation requests."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        mqtt_adapter: MQTTClientAdapter,
        datalogger: DataLoggerService,
        robot_state_repository: RobotStateRepository,
        websocket_hub: WebSocketHub,
    ) -> None:
        self._session = session
        self._mqtt = mqtt_adapter
        self._datalogger = datalogger
        self._robot_states = robot_state_repository
        self._ws_hub = websocket_hub

    async def set_velocity(self, payload: VelocityCommandPayload) -> None:
        topic = f"/amr/{payload.robot_id}/cmd_vel"
        await self._mqtt.publish(topic, payload.__dict__)

        async def persist_state() -> None:
            session_id = await self._datalogger.get_active_session_id(payload.robot_id)
            if not session_id:
                return
            await self._robot_states.create_state(
                robot_id=payload.robot_id,
                status="moving",
                battery_level=100,
                session_id=session_id,
            )
            await self._session.commit()
            await self._ws_hub.broadcast(  # notify UI with latest status
                channel="robot", message={"event": "velocity", "robot_id": payload.robot_id, "linear": payload.linear, "angular": payload.angular}
            )

        asyncio.create_task(persist_state())

    async def send_navigation_goal(self, payload: NavigationGoalPayload) -> None:
        topic = f"/amr/{payload.robot_id}/navigation_goal"
        await self._mqtt.publish(topic, payload.__dict__)
        await self._ws_hub.broadcast(
            channel="robot",
            message={
                "event": "navigation",
                "robot_id": payload.robot_id,
                "target": {
                    "x": payload.target_x,
                    "y": payload.target_y,
                    "orientation": payload.orientation,
                },
            },
        )

    async def toggle_session_recording(
        self, *, robot_id: str, enable: bool, metadata: dict | None = None
    ) -> None:
        if enable:
            await self._datalogger.start_session(robot_id=robot_id, name=f"session-{robot_id}", metadata=metadata)
        else:
            active_id = await self._datalogger.get_active_session_id(robot_id)
            if active_id:
                await self._datalogger.end_session(session_id=active_id, save=True)

