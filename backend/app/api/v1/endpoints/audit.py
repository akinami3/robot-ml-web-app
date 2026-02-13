"""Audit log endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..dependencies import AdminUser, AuditRepo
from ..schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: AdminUser,
    audit_repo: AuditRepo,
    offset: int = 0,
    limit: int = 100,
):
    logs = await audit_repo.get_all(offset=offset, limit=limit)
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action.value if hasattr(log.action, "value") else log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        )
        for log in logs
    ]
