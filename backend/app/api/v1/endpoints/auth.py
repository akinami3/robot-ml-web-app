"""Authentication endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from ....config import Settings, get_settings
from ....core.security import create_tokens, hash_password, verify_password
from ....domain.entities.audit_log import AuditAction
from ....domain.entities.user import User, UserRole
from ..dependencies import AuditSvc, CurrentUser, UserRepo
from ..schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    user_repo: UserRepo,
    audit_svc: AuditSvc,
):
    user = await user_repo.get_by_username(body.username)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    settings = get_settings()
    tokens = create_tokens(
        user_id=str(user.id),
        role=user.role.value,
        private_key=settings.jwt_private_key,
        access_expire_minutes=settings.jwt_access_expire_minutes,
        refresh_expire_days=settings.jwt_refresh_expire_days,
    )

    await audit_svc.log_action(
        user_id=user.id,
        action=AuditAction.LOGIN,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=settings.jwt_access_expire_minutes * 60,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserCreate,
    user_repo: UserRepo,
):
    # Check existing
    existing = await user_repo.get_by_username(body.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    existing_email = await user_repo.get_by_email(body.email)
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
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
    return UserResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        role=created.role.value,
        is_active=created.is_active,
        created_at=created.created_at,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    user_repo: UserRepo,
):
    from ....core.security import decode_token

    settings = get_settings()
    payload = decode_token(body.refresh_token, settings.jwt_public_key)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    from uuid import UUID

    user = await user_repo.get_by_id(UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    tokens = create_tokens(
        user_id=str(user.id),
        role=user.role.value,
        private_key=settings.jwt_private_key,
        access_expire_minutes=settings.jwt_access_expire_minutes,
        refresh_expire_days=settings.jwt_refresh_expire_days,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=settings.jwt_access_expire_minutes * 60,
    )
