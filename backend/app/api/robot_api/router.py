"""Robot API endpoints bridging frontend commands to MQTT."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_robot_control_service
from app.schemas.robot import (
    NavigationGoal,
    RobotCommandResponse,
    SimulationToggleRequest,
    VelocityCommand,
)
from app.services.robot_control import NavigationGoalPayload, RobotControlService, VelocityCommandPayload

router = APIRouter()


@router.post("/velocity", status_code=status.HTTP_202_ACCEPTED, response_model=RobotCommandResponse)
async def set_velocity(
    command: VelocityCommand,
    service: RobotControlService = Depends(get_robot_control_service),
) -> RobotCommandResponse:
    payload = VelocityCommandPayload(
        robot_id=command.robot_id,
        linear=command.linear,
        angular=command.angular,
    )
    asyncio.create_task(service.set_velocity(payload))
    return RobotCommandResponse()


@router.post("/navigation", status_code=status.HTTP_202_ACCEPTED, response_model=RobotCommandResponse)
async def send_navigation(
    goal: NavigationGoal,
    service: RobotControlService = Depends(get_robot_control_service),
) -> RobotCommandResponse:
    payload = NavigationGoalPayload(
        robot_id=goal.robot_id,
        target_x=goal.target_x,
        target_y=goal.target_y,
        orientation=goal.orientation,
    )
    await service.send_navigation_goal(payload)
    return RobotCommandResponse()


@router.post("/session", response_model=RobotCommandResponse)
async def toggle_session(
    body: SimulationToggleRequest,
    service: RobotControlService = Depends(get_robot_control_service),
) -> RobotCommandResponse:
    await service.toggle_session_recording(robot_id=body.robot_id, enable=body.enable, metadata=body.metadata)
    return RobotCommandResponse(status="ok" if body.enable else "stopped")
