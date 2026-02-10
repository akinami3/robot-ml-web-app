"""
Command Data REST API Router

保存済みコマンド（制御値）データの照会・エクスポート用REST API
ML学習データとしてセンサデータと組み合わせて利用する
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.database import get_db
from app.models.command_data import CommandDataRecord

router = APIRouter(prefix="/command-data", tags=["Command Data"])


# Schemas
class CommandDataResponse(BaseModel):
    id: int
    robot_id: str
    recorded_at: datetime
    command: str
    parameters: dict
    user_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    robot_state_before: dict
    created_at: datetime

    class Config:
        from_attributes = True


class CommandDataListResponse(BaseModel):
    total: int
    records: List[CommandDataResponse]


class CommandDataStats(BaseModel):
    robot_id: str
    total_commands: int
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None
    success_count: int
    failure_count: int


class CommandTypeStats(BaseModel):
    command: str
    count: int
    success_rate: float


@router.get("", response_model=CommandDataListResponse)
async def get_command_data(
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    command: Optional[str] = Query(None, description="Filter by command type (move, stop, etc.)"),
    success: Optional[bool] = Query(None, description="Filter by success/failure"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get recorded command data with optional filters"""
    conditions = []
    if robot_id:
        conditions.append(CommandDataRecord.robot_id == robot_id)
    if user_id:
        conditions.append(CommandDataRecord.user_id == user_id)
    if command:
        conditions.append(CommandDataRecord.command == command)
    if success is not None:
        conditions.append(CommandDataRecord.success == success)
    if start_time:
        conditions.append(CommandDataRecord.recorded_at >= start_time)
    if end_time:
        conditions.append(CommandDataRecord.recorded_at <= end_time)

    where_clause = and_(*conditions) if conditions else True

    # Count
    count_query = select(func.count(CommandDataRecord.id)).where(where_clause)
    total = (await db.execute(count_query)).scalar()

    # Data
    data_query = (
        select(CommandDataRecord)
        .where(where_clause)
        .order_by(CommandDataRecord.recorded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(data_query)
    records = result.scalars().all()

    return CommandDataListResponse(
        total=total,
        records=[CommandDataResponse.model_validate(r) for r in records],
    )


@router.get("/stats", response_model=List[CommandDataStats])
async def get_command_data_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about recorded command data per robot"""
    query = (
        select(
            CommandDataRecord.robot_id,
            func.count(CommandDataRecord.id).label("total_commands"),
            func.min(CommandDataRecord.recorded_at).label("earliest"),
            func.max(CommandDataRecord.recorded_at).label("latest"),
            func.count(CommandDataRecord.id).filter(
                CommandDataRecord.success == True  # noqa: E712
            ).label("success_count"),
            func.count(CommandDataRecord.id).filter(
                CommandDataRecord.success == False  # noqa: E712
            ).label("failure_count"),
        )
        .group_by(CommandDataRecord.robot_id)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        CommandDataStats(
            robot_id=row.robot_id,
            total_commands=row.total_commands,
            earliest=row.earliest,
            latest=row.latest,
            success_count=row.success_count,
            failure_count=row.failure_count,
        )
        for row in rows
    ]


@router.get("/command-types", response_model=List[CommandTypeStats])
async def get_command_type_stats(
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get command type distribution statistics"""
    conditions = []
    if robot_id:
        conditions.append(CommandDataRecord.robot_id == robot_id)

    where_clause = and_(*conditions) if conditions else True

    query = (
        select(
            CommandDataRecord.command,
            func.count(CommandDataRecord.id).label("count"),
            func.count(CommandDataRecord.id).filter(
                CommandDataRecord.success == True  # noqa: E712
            ).label("success_count"),
        )
        .where(where_clause)
        .group_by(CommandDataRecord.command)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        CommandTypeStats(
            command=row.command,
            count=row.count,
            success_rate=(row.success_count / row.count * 100) if row.count > 0 else 0,
        )
        for row in rows
    ]


@router.get("/training-pairs")
async def get_training_pairs(
    robot_id: str = Query(..., description="Robot ID"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """
    Get (state, action) training pairs for ML.
    
    Returns command records with robot_state_before (state) and 
    command+parameters (action), suitable for imitation learning.
    """
    from app.models.sensor_data import SensorDataRecord

    conditions = [CommandDataRecord.robot_id == robot_id, CommandDataRecord.success == True]  # noqa: E712
    if start_time:
        conditions.append(CommandDataRecord.recorded_at >= start_time)
    if end_time:
        conditions.append(CommandDataRecord.recorded_at <= end_time)

    # Get commands with their pre-state
    cmd_query = (
        select(CommandDataRecord)
        .where(and_(*conditions))
        .order_by(CommandDataRecord.recorded_at.asc())
        .limit(limit)
    )
    cmd_result = await db.execute(cmd_query)
    commands = cmd_result.scalars().all()

    training_pairs = []
    for cmd in commands:
        pair = {
            "timestamp": cmd.recorded_at.isoformat(),
            "state": cmd.robot_state_before,
            "action": {
                "command": cmd.command,
                "parameters": cmd.parameters,
            },
            "user_id": cmd.user_id,
        }
        training_pairs.append(pair)

    return {
        "robot_id": robot_id,
        "total_pairs": len(training_pairs),
        "pairs": training_pairs,
    }


@router.delete("/{robot_id}")
async def delete_command_data(
    robot_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Delete command data for a specific robot"""
    from sqlalchemy import delete

    conditions = [CommandDataRecord.robot_id == robot_id]
    if start_time:
        conditions.append(CommandDataRecord.recorded_at >= start_time)
    if end_time:
        conditions.append(CommandDataRecord.recorded_at <= end_time)

    stmt = delete(CommandDataRecord).where(and_(*conditions))
    result = await db.execute(stmt)
    await db.commit()

    return {"deleted_count": result.rowcount}
