"""Sensor data endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from ....domain.entities.sensor_data import SensorType
from ..dependencies import CurrentUser, SensorDataRepo
from ..schemas import AggregatedDataQuery, SensorDataQuery, SensorDataResponse

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("/data", response_model=list[SensorDataResponse])
async def query_sensor_data(
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
    robot_id: UUID,
    sensor_type: str | None = None,
    limit: int = 100,
):
    st = None
    if sensor_type:
        try:
            st = SensorType(sensor_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sensor type: {sensor_type}",
            )

    data = await sensor_repo.get_by_robot(
        robot_id=robot_id,
        sensor_type=st,
        limit=limit,
    )
    return [
        SensorDataResponse(
            id=d.id,
            robot_id=d.robot_id,
            sensor_type=d.sensor_type.value,
            data=d.data,
            timestamp=d.timestamp,
            session_id=d.session_id,
            sequence_number=d.sequence_number,
        )
        for d in data
    ]


@router.get("/data/latest", response_model=SensorDataResponse | None)
async def get_latest_sensor_data(
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
    robot_id: UUID,
    sensor_type: str,
):
    try:
        st = SensorType(sensor_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensor type: {sensor_type}",
        )

    data = await sensor_repo.get_latest(robot_id, st)
    if data is None:
        return None

    return SensorDataResponse(
        id=data.id,
        robot_id=data.robot_id,
        sensor_type=data.sensor_type.value,
        data=data.data,
        timestamp=data.timestamp,
        session_id=data.session_id,
        sequence_number=data.sequence_number,
    )


@router.post("/data/aggregated")
async def get_aggregated_data(
    body: AggregatedDataQuery,
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
):
    try:
        st = SensorType(body.sensor_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensor type: {body.sensor_type}",
        )

    return await sensor_repo.get_aggregated(
        robot_id=body.robot_id,
        sensor_type=st,
        start_time=body.start_time,
        end_time=body.end_time,
        bucket_seconds=body.bucket_seconds,
    )


@router.get("/types")
async def list_sensor_types(current_user: CurrentUser):
    return [{"value": st.value, "name": st.name} for st in SensorType]
