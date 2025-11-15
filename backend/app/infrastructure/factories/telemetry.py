"""Factories for telemetry-related use cases."""

from __future__ import annotations

from app.application.interfaces import UnitOfWork, WebSocketBroadcaster
from app.application.use_cases.telemetry import DataLoggerUseCase, TelemetryProcessorUseCase
from app.repositories.dataset_sessions import DatasetSessionRepository
from app.repositories.sensor_data import SensorDataRepository


def build_datalogger(unit_of_work: UnitOfWork) -> DataLoggerUseCase:
    dataset_repo = DatasetSessionRepository(unit_of_work.session)
    sensor_repo = SensorDataRepository(unit_of_work.session)
    return DataLoggerUseCase(
        unit_of_work=unit_of_work,
        dataset_repo=dataset_repo,
        sensor_repo=sensor_repo,
    )


def build_telemetry_processor(
    *,
    unit_of_work: UnitOfWork,
    websocket_hub: WebSocketBroadcaster,
    datalogger: DataLoggerUseCase | None = None,
) -> TelemetryProcessorUseCase:
    datalogger = datalogger or build_datalogger(unit_of_work)
    return TelemetryProcessorUseCase(
        datalogger=datalogger,
        websocket_hub=websocket_hub,
    )


__all__ = ["build_datalogger", "build_telemetry_processor"]
