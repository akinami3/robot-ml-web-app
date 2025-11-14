"""Application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters import LLMClientAdapter, MQTTClientAdapter, VectorStoreAdapter
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import get_session_factory
from app.features.telemetry.dependencies import (
    create_datalogger_service,
    create_telemetry_processor_service,
)
from app.infrastructure.messaging import TELEMETRY_SUBSCRIPTION_PATTERN
from app.infrastructure.realtime import WebSocketHub
from app.infrastructure.realtime.handlers import router as websocket_router
from app.workers.celery_app import get_celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
	configure_logging()
	mqtt_adapter = MQTTClientAdapter()
	websocket_hub = WebSocketHub()
	vector_store = VectorStoreAdapter()
	llm_client = LLMClientAdapter()
	celery_app = get_celery_app()

	await mqtt_adapter.connect()

	app.state.mqtt_adapter = mqtt_adapter
	app.state.websocket_hub = websocket_hub
	app.state.vector_store = vector_store
	app.state.llm_client = llm_client
	app.state.celery_app = celery_app

	session_factory = get_session_factory()

	async def telemetry_callback(topic: str, payload: dict[str, Any]) -> None:
		parts = topic.strip("/").split("/")
		robot_id = parts[1] if len(parts) > 1 else "unknown"
		sensor_type = parts[-1]
		async with session_factory() as session:
			datalogger = create_datalogger_service(session)
			telemetry_service = create_telemetry_processor_service(
				session=session,
				datalogger=datalogger,
				websocket_hub=websocket_hub,
			)
			await telemetry_service.handle_mqtt_message(
				robot_id=robot_id,
				sensor_type=sensor_type,
				payload=payload,
			)

	await mqtt_adapter.subscribe_with_callback(TELEMETRY_SUBSCRIPTION_PATTERN, telemetry_callback)

	try:
		yield
	finally:
		await mqtt_adapter.disconnect()
		await llm_client.close()


app = FastAPI(title=settings.project_name, lifespan=lifespan)

if settings.backend_cors_origins:
	origins = [str(origin) for origin in settings.backend_cors_origins]
else:
	origins = ["http://localhost:3000"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(websocket_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
	return {"status": "ok"}
