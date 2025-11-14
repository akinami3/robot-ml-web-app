"""Dependency wiring for the telemetry feature."""

from __future__ import annotations

from fastapi import Depends, Request

from app.application.interfaces import UnitOfWork, WebSocketBroadcaster
from app.application.use_cases.telemetry import (
    DataLoggerUseCase,
    TelemetryProcessorUseCase,
    create_datalogger_use_case,
    create_telemetry_processor_use_case,
)
from app.core.base_dependencies import (
    get_unit_of_work,
    get_websocket_hub,
)
from .service import DataLoggerService, TelemetryProcessorService


__all__ = [
    "create_datalogger_service",
    "create_telemetry_processor_service",
    "get_datalogger_service",
    "get_telemetry_processor_service",
]


def create_datalogger_service(unit_of_work: UnitOfWork) -> DataLoggerService:
    return create_datalogger_use_case(unit_of_work=unit_of_work)


def create_telemetry_processor_service(
    *,
    unit_of_work: UnitOfWork,
    websocket_hub: WebSocketBroadcaster,
    datalogger: DataLoggerUseCase | None = None,
) -> TelemetryProcessorService:
    return create_telemetry_processor_use_case(
        unit_of_work=unit_of_work,
        websocket_hub=websocket_hub,
        datalogger=datalogger,
    )


async def get_datalogger_service(
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> DataLoggerService:
    return create_datalogger_service(unit_of_work)


async def get_telemetry_processor_service(
    request: Request,
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
    datalogger: DataLoggerService = Depends(get_datalogger_service),
) -> TelemetryProcessorService:
    return create_telemetry_processor_service(
        unit_of_work=unit_of_work,
        datalogger=datalogger,
        websocket_hub=get_websocket_hub(request),
    )
