from __future__ import annotations

import logging
from typing import Sequence

from sqlalchemy.orm import Session

from app.infrastructure.mqtt.client import MQTTClient
from app.infrastructure.mqtt import topics
from app.repositories.robot_repository import RobotRepository
from app.schemas.robot import NavigationCommand, RobotDevice, VelocityCommand

logger = logging.getLogger(__name__)


class RobotControlService:
    def __init__(self, db: Session, mqtt_client: MQTTClient) -> None:
        self._db = db
        self._mqtt_client = mqtt_client
        self._repository = RobotRepository(db)

    async def send_velocity_command(self, command: VelocityCommand) -> None:
        payload = {
            "vx": command.linear_x,
            "vy": command.linear_y,
            "omega": command.angular_z,
        }
        logger.debug("Sending velocity command %s", payload)
        await self._mqtt_client.publish(topics.ROBOT_VELOCITY_CMD, payload)

    async def send_navigation_command(self, command: NavigationCommand) -> None:
        payload = {
            "goal": {
                "x": command.goal.target_x,
                "y": command.goal.target_y,
                "yaw": command.goal.target_yaw,
            },
            "frame_id": command.frame_id,
        }
        logger.debug("Sending navigation command %s", payload)
        await self._mqtt_client.publish(topics.ROBOT_NAVIGATION_CMD, payload)

    def list_devices(self) -> Sequence[RobotDevice]:
        devices = self._repository.list_devices()
        return [RobotDevice.from_orm(device) for device in devices]
