"""Dependency wiring for the robot feature."""

from __future__ import annotations

from fastapi import Depends, Request

from app.application.interfaces import UnitOfWork
from app.application.use_cases.telemetry import DataLoggerUseCase, create_datalogger_use_case
from app.core.base_dependencies import (
    get_mqtt_adapter,
    get_unit_of_work,
    get_websocket_hub,
)
from app.repositories.robot_state import RobotStateRepository
from .service import RobotControlService


__all__ = ["get_robot_control_service"]


async def get_robot_control_service(
    request: Request,
    unit_of_work: UnitOfWork = Depends(get_unit_of_work),
) -> RobotControlService:
    datalogger: DataLoggerUseCase = create_datalogger_use_case(unit_of_work=unit_of_work)
    return RobotControlService(
        unit_of_work=unit_of_work,
        mqtt_adapter=get_mqtt_adapter(request),
        datalogger=datalogger,
        robot_state_repository=RobotStateRepository(unit_of_work.session),
        websocket_hub=get_websocket_hub(request),
    )
