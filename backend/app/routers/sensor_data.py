"""
Sensor Data REST API Router

保存済みセンサデータの照会・エクスポート用REST API
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.database import get_db
from app.models.sensor_data import SensorDataRecord

router = APIRouter(prefix="/sensor-data", tags=["Sensor Data"])


# Schemas
class SensorDataResponse(BaseModel):
    id: int
    robot_id: str
    recorded_at: datetime
    sensor_data: dict
    control_data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SensorDataListResponse(BaseModel):
    total: int
    records: List[SensorDataResponse]


class SensorDataStats(BaseModel):
    robot_id: str
    total_records: int
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None


@router.get("", response_model=SensorDataListResponse)
async def get_sensor_data(
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get recorded sensor data with optional filters"""
    conditions = []
    if robot_id:
        conditions.append(SensorDataRecord.robot_id == robot_id)
    if start_time:
        conditions.append(SensorDataRecord.recorded_at >= start_time)
    if end_time:
        conditions.append(SensorDataRecord.recorded_at <= end_time)

    where_clause = and_(*conditions) if conditions else True

    # Count
    count_query = select(func.count(SensorDataRecord.id)).where(where_clause)
    total = (await db.execute(count_query)).scalar()

    # Data
    data_query = (
        select(SensorDataRecord)
        .where(where_clause)
        .order_by(SensorDataRecord.recorded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(data_query)
    records = result.scalars().all()

    return SensorDataListResponse(
        total=total,
        records=[SensorDataResponse.model_validate(r) for r in records],
    )


@router.get("/stats", response_model=List[SensorDataStats])
async def get_sensor_data_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get statistics about recorded sensor data per robot"""
    query = (
        select(
            SensorDataRecord.robot_id,
            func.count(SensorDataRecord.id).label("total_records"),
            func.min(SensorDataRecord.recorded_at).label("earliest"),
            func.max(SensorDataRecord.recorded_at).label("latest"),
        )
        .group_by(SensorDataRecord.robot_id)
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        SensorDataStats(
            robot_id=row.robot_id,
            total_records=row.total_records,
            earliest=row.earliest,
            latest=row.latest,
        )
        for row in rows
    ]


@router.delete("/{robot_id}")
async def delete_sensor_data(
    robot_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Delete sensor data for a specific robot"""
    from sqlalchemy import delete

    conditions = [SensorDataRecord.robot_id == robot_id]
    if start_time:
        conditions.append(SensorDataRecord.recorded_at >= start_time)
    if end_time:
        conditions.append(SensorDataRecord.recorded_at <= end_time)

    stmt = delete(SensorDataRecord).where(and_(*conditions))
    result = await db.execute(stmt)
    await db.commit()

    return {"deleted_count": result.rowcount}
