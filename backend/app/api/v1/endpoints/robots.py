"""Robot management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ....domain.entities.audit_log import AuditAction
from ....domain.entities.robot import Robot
from ..dependencies import AuditSvc, CurrentUser, OperatorUser, RobotRepo
from ..schemas import RobotCreate, RobotResponse, RobotUpdate

router = APIRouter(prefix="/robots", tags=["robots"])


@router.get("", response_model=list[RobotResponse])
async def list_robots(
    current_user: CurrentUser,
    robot_repo: RobotRepo,
    offset: int = 0,
    limit: int = 100,
):
    robots = await robot_repo.get_all(offset=offset, limit=limit)
    return [
        RobotResponse(
            id=r.id,
            name=r.name,
            adapter_type=r.adapter_type,
            state=r.state.value,
            capabilities=[c.value for c in r.capabilities],
            battery_level=r.battery_level,
            last_seen=r.last_seen,
            created_at=r.created_at,
        )
        for r in robots
    ]


@router.get("/{robot_id}", response_model=RobotResponse)
async def get_robot(
    robot_id: UUID,
    current_user: CurrentUser,
    robot_repo: RobotRepo,
):
    robot = await robot_repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")
    return RobotResponse(
        id=robot.id,
        name=robot.name,
        adapter_type=robot.adapter_type,
        state=robot.state.value,
        capabilities=[c.value for c in robot.capabilities],
        battery_level=robot.battery_level,
        last_seen=robot.last_seen,
        created_at=robot.created_at,
    )


@router.post("", response_model=RobotResponse, status_code=201)
async def create_robot(
    body: RobotCreate,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
    audit_svc: AuditSvc,
):
    existing = await robot_repo.get_by_name(body.name)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Robot name already exists",
        )

    robot = Robot(
        name=body.name,
        adapter_type=body.adapter_type,
        connection_params=body.connection_params,
    )
    created = await robot_repo.create(robot)

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.ROBOT_CONNECT,
        resource_type="robot",
        resource_id=str(created.id),
    )

    return RobotResponse(
        id=created.id,
        name=created.name,
        adapter_type=created.adapter_type,
        state=created.state.value,
        capabilities=[c.value for c in created.capabilities],
        battery_level=created.battery_level,
        last_seen=created.last_seen,
        created_at=created.created_at,
    )


@router.patch("/{robot_id}", response_model=RobotResponse)
async def update_robot(
    robot_id: UUID,
    body: RobotUpdate,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
):
    robot = await robot_repo.get_by_id(robot_id)
    if robot is None:
        raise HTTPException(status_code=404, detail="Robot not found")

    if body.name is not None:
        robot.name = body.name
    if body.connection_params is not None:
        robot.connection_params = body.connection_params

    updated = await robot_repo.update(robot)
    return RobotResponse(
        id=updated.id,
        name=updated.name,
        adapter_type=updated.adapter_type,
        state=updated.state.value,
        capabilities=[c.value for c in updated.capabilities],
        battery_level=updated.battery_level,
        last_seen=updated.last_seen,
        created_at=updated.created_at,
    )


@router.delete("/{robot_id}", status_code=204)
async def delete_robot(
    robot_id: UUID,
    current_user: OperatorUser,
    robot_repo: RobotRepo,
    audit_svc: AuditSvc,
):
    deleted = await robot_repo.delete(robot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Robot not found")

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.ROBOT_DISCONNECT,
        resource_type="robot",
        resource_id=str(robot_id),
    )
