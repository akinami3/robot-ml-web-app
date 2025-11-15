"""Robot control application use cases."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.events import ROBOT_CHANNEL, RobotEvent
from app.application.interfaces import (
    MQTTPublisher,
    RobotStateRepositoryProtocol,
    UnitOfWork,
    WebSocketBroadcaster,
)
from app.application.use_cases.telemetry import DataLoggerUseCase
from app.infrastructure.messaging import (
    navigation_command_topic,
    velocity_command_topic,
)


@dataclass(slots=True)
class VelocityCommandPayload:
    robot_id: str
    linear: float
    angular: float


@dataclass(slots=True)
class NavigationGoalPayload:
    robot_id: str
    target_x: float
    target_y: float
    orientation: float


class RobotControlUseCase:
    """Coordinates robot actuation requests across transport layers."""

    def __init__(
        self,
        *,
        unit_of_work: UnitOfWork,
        mqtt_adapter: MQTTPublisher,
        datalogger: DataLoggerUseCase,
        robot_state_repository: RobotStateRepositoryProtocol,
        websocket_hub: WebSocketBroadcaster,
    ) -> None:
        self._uow = unit_of_work
        self._mqtt = mqtt_adapter
        self._datalogger = datalogger
        self._robot_states = robot_state_repository
        self._ws_hub = websocket_hub

    async def set_velocity(self, payload: VelocityCommandPayload) -> None:
        topic = velocity_command_topic(payload.robot_id)
        await self._mqtt.publish(topic, payload.__dict__)

        session_id = await self._datalogger.get_active_session_id(payload.robot_id)
        if not session_id:
            return

        async with self._uow:
            await self._robot_states.create_state(
                robot_id=payload.robot_id,
                status="moving",
                battery_level=100,
                session_id=session_id,
            )
        await self._ws_hub.broadcast(
            channel=ROBOT_CHANNEL,
            message={
                "event": RobotEvent.VELOCITY.value,
                "robot_id": payload.robot_id,
                "linear": payload.linear,
                "angular": payload.angular,
            },
        )

    async def send_navigation_goal(self, payload: NavigationGoalPayload) -> None:
        topic = navigation_command_topic(payload.robot_id)
        await self._mqtt.publish(topic, payload.__dict__)
        await self._ws_hub.broadcast(
            channel=ROBOT_CHANNEL,
            message={
                "event": RobotEvent.NAVIGATION.value,
                "robot_id": payload.robot_id,
                "target": {
                    "x": payload.target_x,
                    "y": payload.target_y,
                    "orientation": payload.orientation,
                },
            },
        )

    async def toggle_session_recording(
        self,
        *,
        robot_id: str,
        enable: bool,
        metadata: dict | None = None,
    ) -> None:
        if enable:
            await self._datalogger.start_session(
                robot_id=robot_id,
                name=f"session-{robot_id}",
                metadata=metadata,
            )
        else:
            active_id = await self._datalogger.get_active_session_id(robot_id)
            if active_id:
                await self._datalogger.end_session(session_id=active_id, save=True)


__all__ = [
    "VelocityCommandPayload",
    "NavigationGoalPayload",
    "RobotControlUseCase",
]
