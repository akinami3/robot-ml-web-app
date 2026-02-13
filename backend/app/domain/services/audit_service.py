"""Audit service - domain logic for audit logging."""

from __future__ import annotations

import structlog
from uuid import UUID

from ..entities.audit_log import AuditAction, AuditLog
from ..repositories.audit_repository import AuditRepository

logger = structlog.get_logger()


class AuditService:
    def __init__(self, audit_repo: AuditRepository) -> None:
        self._repo = audit_repo

    async def log_action(
        self,
        user_id: UUID,
        action: AuditAction,
        resource_type: str = "",
        resource_id: str = "",
        details: dict | None = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        created = await self._repo.create(entry)
        logger.info(
            "audit_log_created",
            action=action.value,
            user_id=str(user_id),
            resource_type=resource_type,
            resource_id=resource_id,
        )
        return created

    async def get_user_history(
        self, user_id: UUID, limit: int = 100
    ) -> list[AuditLog]:
        return await self._repo.get_by_user(user_id, limit=limit)

    async def get_resource_history(
        self, resource_type: str, resource_id: str
    ) -> list[AuditLog]:
        return await self._repo.get_by_resource(resource_type, resource_id)
