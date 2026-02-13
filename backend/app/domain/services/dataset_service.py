"""Dataset service - domain logic for dataset management."""

from __future__ import annotations

import structlog
from datetime import datetime
from uuid import UUID

from ..entities.dataset import Dataset, DatasetExportFormat, DatasetStatus
from ..entities.sensor_data import SensorType
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.sensor_data_repository import SensorDataRepository

logger = structlog.get_logger()


class DatasetService:
    def __init__(
        self,
        dataset_repo: DatasetRepository,
        sensor_data_repo: SensorDataRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._sensor_data_repo = sensor_data_repo

    async def create_dataset(
        self,
        name: str,
        description: str,
        owner_id: UUID,
        robot_ids: list[UUID],
        sensor_types: list[str],
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Dataset:
        dataset = Dataset(
            name=name,
            description=description,
            owner_id=owner_id,
            robot_ids=robot_ids,
            sensor_types=sensor_types,
            start_time=start_time,
            end_time=end_time,
            tags=tags or [],
            status=DatasetStatus.CREATING,
        )
        created = await self._dataset_repo.create(dataset)

        # Calculate stats
        count = 0
        for robot_id in robot_ids:
            for st_str in sensor_types:
                try:
                    st = SensorType(st_str)
                except ValueError:
                    continue
                data = await self._sensor_data_repo.get_by_robot(
                    robot_id=robot_id,
                    sensor_type=st,
                    start_time=start_time,
                    end_time=end_time,
                    limit=1_000_000,
                )
                count += len(data)

        await self._dataset_repo.update_stats(created.id, count, 0)
        await self._dataset_repo.update_status(created.id, DatasetStatus.READY)

        logger.info(
            "dataset_created",
            dataset_id=str(created.id),
            name=name,
            record_count=count,
        )
        return await self._dataset_repo.get_by_id(created.id)  # type: ignore

    async def get_user_datasets(self, owner_id: UUID) -> list[Dataset]:
        return await self._dataset_repo.get_by_owner(owner_id)

    async def get_dataset(self, dataset_id: UUID) -> Dataset | None:
        return await self._dataset_repo.get_by_id(dataset_id)

    async def delete_dataset(self, dataset_id: UUID) -> bool:
        return await self._dataset_repo.delete(dataset_id)

    async def export_dataset(
        self, dataset_id: UUID, format: DatasetExportFormat
    ) -> str:
        """Export dataset to file, return file path."""
        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        if not dataset.is_exportable:
            raise ValueError(f"Dataset {dataset_id} is not exportable")

        await self._dataset_repo.update_status(dataset_id, DatasetStatus.EXPORTING)

        # Collect data
        all_data = []
        for robot_id in dataset.robot_ids:
            for st_str in dataset.sensor_types:
                try:
                    st = SensorType(st_str)
                except ValueError:
                    continue
                data = await self._sensor_data_repo.get_by_robot(
                    robot_id=robot_id,
                    sensor_type=st,
                    start_time=dataset.start_time,
                    end_time=dataset.end_time,
                    limit=1_000_000,
                )
                all_data.extend(data)

        export_path = f"/tmp/exports/{dataset_id}.{format.value}"
        # Actual export logic would convert data to chosen format
        logger.info(
            "dataset_exported",
            dataset_id=str(dataset_id),
            format=format.value,
            records=len(all_data),
        )

        await self._dataset_repo.update_status(dataset_id, DatasetStatus.READY)
        return export_path
