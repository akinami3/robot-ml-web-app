"""
Robots Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.database import get_db
from app.models import Robot, User
from app.schemas import (
    RobotCreate, RobotUpdate, RobotResponse, RobotListResponse, 
    MoveCommand, StopCommand, CommandResponse
)
from app.auth import get_current_user, get_current_operator_or_admin
from app.services.gateway_client import GatewayClient

router = APIRouter(prefix="/robots", tags=["Robots"])


@router.get("", response_model=RobotListResponse)
async def list_robots(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    vendor: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all robots with optional filters"""
    query = select(Robot)
    
    if vendor:
        query = query.where(Robot.vendor == vendor)
    if state:
        query = query.where(Robot.state == state)
    
    # Get total count
    count_query = select(func.count()).select_from(Robot)
    if vendor:
        count_query = count_query.where(Robot.vendor == vendor)
    if state:
        count_query = count_query.where(Robot.state == state)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get robots
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    robots = result.scalars().all()
    
    return RobotListResponse(total=total, robots=robots)


@router.post("", response_model=RobotResponse, status_code=status.HTTP_201_CREATED)
async def create_robot(
    robot_data: RobotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Create a new robot"""
    # Check if robot_id exists
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_data.robot_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Robot ID already exists"
        )
    
    robot = Robot(
        robot_id=robot_data.robot_id,
        name=robot_data.name,
        vendor=robot_data.vendor,
        model=robot_data.model,
        capabilities=robot_data.capabilities.model_dump() if robot_data.capabilities else {}
    )
    db.add(robot)
    await db.commit()
    await db.refresh(robot)
    
    return robot


@router.get("/{robot_id}", response_model=RobotResponse)
async def get_robot(
    robot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a robot by ID"""
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    return robot


@router.put("/{robot_id}", response_model=RobotResponse)
async def update_robot(
    robot_id: str,
    robot_data: RobotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Update a robot"""
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    update_data = robot_data.model_dump(exclude_unset=True)
    if "capabilities" in update_data and update_data["capabilities"]:
        update_data["capabilities"] = update_data["capabilities"].model_dump()
    
    for field, value in update_data.items():
        setattr(robot, field, value)
    
    await db.commit()
    await db.refresh(robot)
    
    return robot


@router.delete("/{robot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_robot(
    robot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Delete a robot"""
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    await db.delete(robot)
    await db.commit()


@router.post("/{robot_id}/move", response_model=CommandResponse)
async def move_robot(
    robot_id: str,
    command: MoveCommand,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Send move command to robot"""
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    if not robot.is_online:
        raise HTTPException(status_code=400, detail="Robot is offline")
    
    # Send command to gateway
    gateway_client = GatewayClient()
    response = await gateway_client.send_move_command(
        robot_id=robot_id,
        goal_x=command.goal.x,
        goal_y=command.goal.y,
        goal_theta=command.goal.theta
    )
    
    return response


@router.post("/{robot_id}/stop", response_model=CommandResponse)
async def stop_robot(
    robot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Send stop command to robot"""
    result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    # Send command to gateway
    gateway_client = GatewayClient()
    response = await gateway_client.send_stop_command(robot_id=robot_id)
    
    return response
