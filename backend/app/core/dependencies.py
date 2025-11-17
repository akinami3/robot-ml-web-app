from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.infrastructure.database.session import SessionLocal
from app.infrastructure.mqtt.client import MQTTClient
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager
from app.services.robot_control_service import RobotControlService


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mqtt_client(request: Request) -> MQTTClient:
    return request.app.state.mqtt_client


def get_robot_control_service(
    db: Session = Depends(get_db),
    mqtt_client: MQTTClient = Depends(get_mqtt_client),
) -> RobotControlService:
    return RobotControlService(db, mqtt_client)


def get_ws_manager(request: Request) -> WebSocketConnectionManager:
    return request.app.state.ws_manager
