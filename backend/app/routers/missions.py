"""
Missions Router
"""
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.database import get_db
from app.models import Mission, Robot, User
from app.schemas import MissionCreate, MissionResponse, MissionListResponse
from app.auth import get_current_user, get_current_operator_or_admin
from app.services.gateway_client import GatewayClient

router = APIRouter(prefix="/missions", tags=["Missions"])


@router.get("", response_model=MissionListResponse)
async def list_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    robot_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all missions with optional filters"""
    query = select(Mission)
    
    if status:
        query = query.where(Mission.status == status)
    if robot_id:
        robot_result = await db.execute(select(Robot).where(Robot.robot_id == robot_id))
        robot = robot_result.scalar_one_or_none()
        if robot:
            query = query.where(Mission.robot_id == robot.id)
    
    # Get total count
    count_query = select(func.count()).select_from(Mission)
    if status:
        count_query = count_query.where(Mission.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get missions
    query = query.order_by(Mission.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    missions = result.scalars().all()
    
    return MissionListResponse(total=total, missions=missions)


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    mission_data: MissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Create a new mission"""
    # Get robot
    result = await db.execute(select(Robot).where(Robot.robot_id == mission_data.robot_id))
    robot = result.scalar_one_or_none()
    
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    if not robot.is_online:
        raise HTTPException(status_code=400, detail="Robot is offline")
    
    # Create mission
    mission = Mission(
        mission_id=f"mission_{uuid4().hex[:8]}",
        name=mission_data.name,
        robot_id=robot.id,
        created_by=current_user.id,
        goal_x=mission_data.goal_x,
        goal_y=mission_data.goal_y,
        goal_theta=mission_data.goal_theta,
        status="PENDING"
    )
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    
    # Send move command to gateway
    gateway_client = GatewayClient()
    try:
        await gateway_client.send_move_command(
            robot_id=mission_data.robot_id,
            goal_x=mission_data.goal_x,
            goal_y=mission_data.goal_y,
            goal_theta=mission_data.goal_theta
        )
        mission.status = "IN_PROGRESS"
        mission.started_at = datetime.utcnow()
        await db.commit()
        await db.refresh(mission)
    except Exception as e:
        mission.status = "FAILED"
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to send command: {str(e)}")
    
    return mission


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a mission by ID"""
    result = await db.execute(select(Mission).where(Mission.mission_id == mission_id))
    mission = result.scalar_one_or_none()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return mission


@router.post("/{mission_id}/cancel", response_model=MissionResponse)
async def cancel_mission(
    mission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator_or_admin)
):
    """Cancel a mission"""
    result = await db.execute(select(Mission).where(Mission.mission_id == mission_id))
    mission = result.scalar_one_or_none()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if mission.status not in ["PENDING", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="Mission cannot be cancelled")
    
    # Get robot
    robot_result = await db.execute(select(Robot).where(Robot.id == mission.robot_id))
    robot = robot_result.scalar_one_or_none()
    
    if robot:
        # Send stop command
        gateway_client = GatewayClient()
        await gateway_client.send_stop_command(robot_id=robot.robot_id)
    
    mission.status = "CANCELLED"
    mission.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(mission)
    
    return mission
