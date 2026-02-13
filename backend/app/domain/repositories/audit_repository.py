"""Audit log repository interface."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from ..entities.audit_log import AuditAction, AuditLog
from .base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        ...

    @abstractmethod
    async def get_by_action(
        self,
        action: AuditAction,
        limit: int = 100,
    ) -> list[AuditLog]:
        ...

    @abstractmethod
    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditLog]:
        ...

    @abstractmethod
    async def delete_older_than(self, before: datetime) -> int:
        ...
