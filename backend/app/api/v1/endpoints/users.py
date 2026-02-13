"""User management endpoints (admin only)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from ....core.security import hash_password
from ....domain.entities.audit_log import AuditAction
from ....domain.entities.user import User, UserRole
from ..dependencies import AdminUser, AuditSvc, UserRepo
from ..schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: AdminUser,
    user_repo: UserRepo,
    offset: int = 0,
    limit: int = 100,
):
    users = await user_repo.get_all(offset=offset, limit=limit)
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: AdminUser,
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    existing = await user_repo.get_by_username(body.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    try:
        role = UserRole(body.role)
    except ValueError:
        role = UserRole.VIEWER

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=role,
    )
    created = await user_repo.create(user)

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.USER_CREATE,
        resource_type="user",
        resource_id=str(created.id),
    )

    return UserResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        role=created.role.value,
        is_active=created.is_active,
        created_at=created.created_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    current_user: AdminUser,
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        try:
            user.role = UserRole(body.role)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role")
    if body.is_active is not None:
        user.is_active = body.is_active

    updated = await user_repo.update(user)

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.USER_UPDATE,
        resource_type="user",
        resource_id=str(user_id),
    )

    return UserResponse(
        id=updated.id,
        username=updated.username,
        email=updated.email,
        role=updated.role.value,
        is_active=updated.is_active,
        created_at=updated.created_at,
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    current_user: AdminUser,
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot delete yourself"
        )

    deleted = await user_repo.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    await audit_svc.log_action(
        user_id=current_user.id,
        action=AuditAction.USER_DELETE,
        resource_type="user",
        resource_id=str(user_id),
    )
