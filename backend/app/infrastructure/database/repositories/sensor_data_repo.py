"""SQLAlchemy implementation of SensorDataRepository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.sensor_data import SensorData, SensorType
from ....domain.repositories.sensor_data_repository import SensorDataRepository
from ..models import SensorDataModel


class SQLAlchemySensorDataRepository(SensorDataRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: SensorDataModel) -> SensorData:
        return SensorData(
            id=model.id,
            robot_id=model.robot_id,
            sensor_type=SensorType(model.sensor_type) if isinstance(model.sensor_type, str) else model.sensor_type,
            data=model.data,
            timestamp=model.timestamp,
            session_id=model.session_id,
            sequence_number=model.sequence_number,
        )

    async def get_by_id(self, id: UUID) -> SensorData | None:
        result = await self._session.get(SensorDataModel, id)
        return self._to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[SensorData]:
        stmt = (
            select(SensorDataModel)
            .order_by(SensorDataModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: SensorData) -> SensorData:
        model = SensorDataModel(
            id=entity.id,
            timestamp=entity.timestamp,
            robot_id=entity.robot_id,
            sensor_type=entity.sensor_type,
            data=entity.data,
            session_id=entity.session_id,
            sequence_number=entity.sequence_number,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: SensorData) -> SensorData:
        raise NotImplementedError("Sensor data is append-only")

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(SensorDataModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(SensorDataModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_robot(
        self,
        robot_id: UUID,
        sensor_type: SensorType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[SensorData]:
        stmt = select(SensorDataModel).where(SensorDataModel.robot_id == robot_id)
        if sensor_type is not None:
            stmt = stmt.where(SensorDataModel.sensor_type == sensor_type)
        if start_time is not None:
            stmt = stmt.where(SensorDataModel.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(SensorDataModel.timestamp <= end_time)
        stmt = stmt.order_by(SensorDataModel.timestamp.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_session(
        self,
        session_id: UUID,
        sensor_type: SensorType | None = None,
    ) -> list[SensorData]:
        stmt = select(SensorDataModel).where(SensorDataModel.session_id == session_id)
        if sensor_type is not None:
            stmt = stmt.where(SensorDataModel.sensor_type == sensor_type)
        stmt = stmt.order_by(SensorDataModel.timestamp.asc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def bulk_insert(self, data: list[SensorData]) -> int:
        models = [
            SensorDataModel(
                id=d.id,
                timestamp=d.timestamp,
                robot_id=d.robot_id,
                sensor_type=d.sensor_type,
                data=d.data,
                session_id=d.session_id,
                sequence_number=d.sequence_number,
            )
            for d in data
        ]
        self._session.add_all(models)
        await self._session.flush()
        return len(models)

    async def get_latest(
        self, robot_id: UUID, sensor_type: SensorType
    ) -> SensorData | None:
        stmt = (
            select(SensorDataModel)
            .where(
                SensorDataModel.robot_id == robot_id,
                SensorDataModel.sensor_type == sensor_type,
            )
            .order_by(SensorDataModel.timestamp.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def count_by_session(self, session_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SensorDataModel)
            .where(SensorDataModel.session_id == session_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_older_than(self, before: datetime) -> int:
        stmt = delete(SensorDataModel).where(SensorDataModel.timestamp < before)
        result = await self._session.execute(stmt)
        return result.rowcount

    async def get_aggregated(
        self,
        robot_id: UUID,
        sensor_type: SensorType,
        start_time: datetime,
        end_time: datetime,
        bucket_seconds: int = 60,
    ) -> list[dict]:
        """Use TimescaleDB time_bucket for aggregation."""
        query = text(
            """
            SELECT
                time_bucket(:bucket || ' seconds', timestamp) AS bucket,
                count(*) AS count,
                avg((data->>'value')::float) AS avg_value,
                min((data->>'value')::float) AS min_value,
                max((data->>'value')::float) AS max_value
            FROM sensor_data
            WHERE robot_id = :robot_id
              AND sensor_type = :sensor_type
              AND timestamp >= :start_time
              AND timestamp <= :end_time
            GROUP BY bucket
            ORDER BY bucket ASC
            """
        )
        result = await self._session.execute(
            query,
            {
                "bucket": str(bucket_seconds),
                "robot_id": str(robot_id),
                "sensor_type": sensor_type.value,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        return [
            {
                "bucket": row.bucket,
                "count": row.count,
                "avg_value": row.avg_value,
                "min_value": row.min_value,
                "max_value": row.max_value,
            }
            for row in result.fetchall()
        ]
