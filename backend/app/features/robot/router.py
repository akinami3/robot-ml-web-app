"""Robot feature API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.core.dependencies import get_robot_control_service
from app.features.robot.schemas import (
    NavigationGoal,
    RobotCommandResponse,
    SimulationToggleRequest,
    VelocityCommand,
)
from app.features.robot.service import (
    NavigationGoalPayload,
    RobotControlService,
    VelocityCommandPayload,
)

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
    await service.set_velocity(payload)
    return RobotCommandResponse()


@router.websocket("/ws")
async def robot_control_channel(
    websocket: WebSocket,
    service: RobotControlService = Depends(get_robot_control_service),
) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("type")
            data = message.get("payload", {})

            if event != "velocity":
                await websocket.send_json(
                    {"type": "error", "reason": "unsupported_event", "received": event}
                )
                continue

            try:
                command = VelocityCommand.model_validate(data)
            except ValidationError as exc:
                await websocket.send_json(
                    {"type": "error", "reason": "invalid_velocity", "details": exc.errors()}
                )
                continue

            payload = VelocityCommandPayload(
                robot_id=command.robot_id,
                linear=command.linear,
                angular=command.angular,
            )
            await service.set_velocity(payload)
            await websocket.send_json({"type": "ack", "event": "velocity", "status": "accepted"})
    except WebSocketDisconnect:
        return


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
    await service.toggle_session_recording(
        robot_id=body.robot_id,
        enable=body.enable,
        metadata=body.metadata,
    )
    return RobotCommandResponse(status="ok" if body.enable else "stopped")
