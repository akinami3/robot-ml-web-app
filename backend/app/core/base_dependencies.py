"""Shared FastAPI dependency helpers used across feature modules."""

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
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.realtime import WebSocketHub


__all__ = [
    "get_db_session",
    "get_unit_of_work",
    "get_mqtt_adapter",
    "get_websocket_hub",
    "get_celery_app",
    "get_llm_client",
    "get_vector_store",
    "get_dataset_session_repository",
    "get_sensor_data_repository",
    "get_training_run_repository",
    "get_training_metric_repository",
    "get_robot_state_repository",
    "get_rag_repository",
]


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in _get_session():
        yield session


async def get_unit_of_work(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session)


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
