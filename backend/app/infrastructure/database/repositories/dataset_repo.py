"""SQLAlchemy implementation of DatasetRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.dataset import Dataset, DatasetExportFormat, DatasetStatus
from ....domain.repositories.dataset_repository import DatasetRepository
from ..models import DatasetModel


class SQLAlchemyDatasetRepository(DatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: DatasetModel) -> Dataset:
        return Dataset(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            status=DatasetStatus(model.status) if isinstance(model.status, str) else model.status,
            sensor_types=model.sensor_types or [],
            robot_ids=model.robot_ids or [],
            start_time=model.start_time,
            end_time=model.end_time,
            record_count=model.record_count,
            size_bytes=model.size_bytes,
            tags=model.tags or [],
            metadata=model.metadata_ or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, id: UUID) -> Dataset | None:
        result = await self._session.get(DatasetModel, id)
        return self._to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[Dataset]:
        stmt = select(DatasetModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: Dataset) -> Dataset:
        model = DatasetModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            owner_id=entity.owner_id,
            status=entity.status,
            sensor_types=entity.sensor_types,
            robot_ids=entity.robot_ids,
            start_time=entity.start_time,
            end_time=entity.end_time,
            record_count=entity.record_count,
            size_bytes=entity.size_bytes,
            tags=entity.tags,
            metadata_=entity.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: Dataset) -> Dataset:
        model = await self._session.get(DatasetModel, entity.id)
        if model is None:
            raise ValueError(f"Dataset {entity.id} not found")
        model.name = entity.name
        model.description = entity.description
        model.status = entity.status
        model.sensor_types = entity.sensor_types
        model.tags = entity.tags
        model.metadata_ = entity.metadata
        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(DatasetModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(DatasetModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_owner(self, owner_id: UUID) -> list[Dataset]:
        stmt = (
            select(DatasetModel)
            .where(DatasetModel.owner_id == owner_id)
            .order_by(DatasetModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_status(self, status: DatasetStatus) -> list[Dataset]:
        stmt = select(DatasetModel).where(DatasetModel.status == status)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update_status(self, dataset_id: UUID, status: DatasetStatus) -> bool:
        stmt = (
            update(DatasetModel)
            .where(DatasetModel.id == dataset_id)
            .values(status=status)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def update_stats(
        self, dataset_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        stmt = (
            update(DatasetModel)
            .where(DatasetModel.id == dataset_id)
            .values(record_count=record_count, size_bytes=size_bytes)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def search_by_tags(self, tags: list[str]) -> list[Dataset]:
        stmt = select(DatasetModel).where(DatasetModel.tags.overlap(tags))
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
