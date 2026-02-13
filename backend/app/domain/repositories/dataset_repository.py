"""Dataset repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from ..entities.dataset import Dataset, DatasetStatus
from .base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> list[Dataset]:
        ...

    @abstractmethod
    async def get_by_status(self, status: DatasetStatus) -> list[Dataset]:
        ...

    @abstractmethod
    async def update_status(self, dataset_id: UUID, status: DatasetStatus) -> bool:
        ...

    @abstractmethod
    async def update_stats(
        self, dataset_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        ...

    @abstractmethod
    async def search_by_tags(self, tags: list[str]) -> list[Dataset]:
        ...
