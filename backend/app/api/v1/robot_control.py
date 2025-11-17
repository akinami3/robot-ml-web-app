from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_robot_control_service
from app.schemas.robot import NavigationCommand, RobotDevice, VelocityCommand
from app.services.robot_control_service import RobotControlService

router = APIRouter(prefix="/robot", tags=["robot"])


@router.get("/devices", response_model=list[RobotDevice])
def list_devices(service: RobotControlService = Depends(get_robot_control_service)):
    return service.list_devices()


@router.post("/control/velocity")
async def send_velocity(
    command: VelocityCommand,
    service: RobotControlService = Depends(get_robot_control_service),
):
    await service.send_velocity_command(command)
    return {"status": "ok"}


@router.post("/control/navigation")
async def send_navigation(
    command: NavigationCommand,
    service: RobotControlService = Depends(get_robot_control_service),
):
    await service.send_navigation_command(command)
    return {"status": "ok"}
