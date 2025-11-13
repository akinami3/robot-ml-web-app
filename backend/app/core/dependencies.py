"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import AsyncIterator

from celery import Celery
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters import LLMClientAdapter, MQTTClientAdapter, VectorStoreAdapter
from app.database.session import get_session as _get_session
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.repositories.rag_documents import RAGDocumentRepository
from app.repositories.robot_state import RobotStateRepository
from app.repositories.sensor_data import SensorDataRepository
from app.repositories.training_metrics import TrainingMetricRepository
from app.repositories.training_runs import TrainingRunRepository
from app.services.chatbot_engine import ChatbotService
from app.services.datalogger import DataLoggerService
from app.services.ml_pipeline import MLPipelineService
from app.services.robot_control import RobotControlService
from app.services.telemetry_processor import TelemetryProcessorService
from app.websocket.manager import WebSocketHub


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in _get_session():
        yield session


def _get_state(request: Request, name: str):
    value = getattr(request.app.state, name, None)
    if value is None:
        raise RuntimeError(f"Application state '{name}' is not initialized")
    return value


def get_mqtt_adapter(request: Request) -> MQTTClientAdapter:
    return _get_state(request, "mqtt_adapter")


def get_websocket_hub(request: Request) -> WebSocketHub:
    return _get_state(request, "websocket_hub")


def get_celery_app(request: Request) -> Celery:
    return _get_state(request, "celery_app")


def get_llm_client(request: Request) -> LLMClientAdapter:
    return _get_state(request, "llm_client")


def get_vector_store(request: Request) -> VectorStoreAdapter:
    return _get_state(request, "vector_store")


async def get_dataset_session_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DatasetSessionRepository:
    return DatasetSessionRepository(session)


async def get_sensor_data_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SensorDataRepository:
    return SensorDataRepository(session)


async def get_training_run_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TrainingRunRepository:
    return TrainingRunRepository(session)


async def get_training_metric_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TrainingMetricRepository:
    return TrainingMetricRepository(session)


async def get_robot_state_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RobotStateRepository:
    return RobotStateRepository(session)


async def get_rag_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RAGDocumentRepository:
    return RAGDocumentRepository(session)


async def get_datalogger_service(
    session: AsyncSession = Depends(get_db_session),
) -> DataLoggerService:
    dataset_repo = DatasetSessionRepository(session)
    sensor_repo = SensorDataRepository(session)
    return DataLoggerService(
        session=session,
        dataset_repo=dataset_repo,
        sensor_repo=sensor_repo,
    )


async def get_robot_control_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RobotControlService:
    return RobotControlService(
        session=session,
        mqtt_adapter=get_mqtt_adapter(request),
        datalogger=await get_datalogger_service(session=session),
        robot_state_repository=RobotStateRepository(session),
        websocket_hub=get_websocket_hub(request),
    )


async def get_telemetry_processor_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> TelemetryProcessorService:
    return TelemetryProcessorService(
        session=session,
        datalogger=await get_datalogger_service(session=session),
        sensor_repo=SensorDataRepository(session),
        websocket_hub=get_websocket_hub(request),
    )


async def get_ml_pipeline_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> MLPipelineService:
    return MLPipelineService(
        session=session,
        training_run_repo=TrainingRunRepository(session),
        training_metric_repo=TrainingMetricRepository(session),
        dataset_repo=DatasetSessionRepository(session),
        websocket_hub=get_websocket_hub(request),
        celery_app=get_celery_app(request),
    )


async def get_chatbot_service(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ChatbotService:
    return ChatbotService(
        session=session,
        rag_repo=RAGDocumentRepository(session),
        vector_store=get_vector_store(request),
        llm_client=get_llm_client(request),
        websocket_hub=get_websocket_hub(request),
    )
