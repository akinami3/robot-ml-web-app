from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import create_db_engine
from app.infrastructure.mqtt.client import MQTTClient
from app.infrastructure.websocket.connection_manager import WebSocketConnectionManager


async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging()
    engine = create_db_engine()
    mqtt_client = MQTTClient(
        broker_url=settings.mqtt_broker_url,
        username=settings.mqtt_username,
        password=settings.mqtt_password,
    )
    ws_manager = WebSocketConnectionManager()

    await mqtt_client.connect()
    app.state.mqtt_client = mqtt_client
    app.state.db_engine = engine
    app.state.ws_manager = ws_manager
    Base.metadata.create_all(bind=engine)

    try:
        yield
    finally:
        await mqtt_client.disconnect()
        engine.dispose()
