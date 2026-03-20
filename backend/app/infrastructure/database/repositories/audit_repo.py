"""SQLAlchemy implementation of AuditRepository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.audit_log import AuditAction, AuditLog
from ....domain.repositories.audit_repository import AuditRepository
from ..models import AuditLogModel


class SQLAlchemyAuditRepository(AuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=model.id,
            user_id=model.user_id,
            action=AuditAction(model.action) if isinstance(model.action, str) else model.action,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            details=model.details or {},
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            timestamp=model.timestamp,
        )

    async def get_by_id(self, id: UUID) -> AuditLog | None:
        result = await self._session.get(AuditLogModel, id)
        return self._to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .order_by(AuditLogModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: AuditLog) -> AuditLog:
        model = AuditLogModel(
            id=entity.id,
            user_id=entity.user_id,
            action=entity.action,
            resource_type=entity.resource_type,
            resource_id=entity.resource_id,
            details=entity.details,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent,
            timestamp=entity.timestamp,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: AuditLog) -> AuditLog:
        raise NotImplementedError("Audit logs are immutable")

    async def delete(self, id: UUID) -> bool:
        raise NotImplementedError("Audit logs should not be deleted individually")

    async def count(self) -> int:
        stmt = select(func.count()).select_from(AuditLogModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_user(
        self,
        user_id: UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        stmt = select(AuditLogModel).where(AuditLogModel.user_id == user_id)
        if start_time:
            stmt = stmt.where(AuditLogModel.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLogModel.timestamp <= end_time)
        stmt = stmt.order_by(AuditLogModel.timestamp.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_action(
        self,
        action: AuditAction,
        limit: int = 100,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.action == action)
            .order_by(AuditLogModel.timestamp.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(
                AuditLogModel.resource_type == resource_type,
                AuditLogModel.resource_id == resource_id,
            )
            .order_by(AuditLogModel.timestamp.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete_older_than(self, before: datetime) -> int:
        stmt = delete(AuditLogModel).where(AuditLogModel.timestamp < before)
        result = await self._session.execute(stmt)
        return result.rowcount
