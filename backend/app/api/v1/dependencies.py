"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import Settings, get_settings
from ...core.security import decode_token
from ...domain.entities.user import User, UserRole
from ...domain.repositories.audit_repository import AuditRepository
from ...domain.repositories.dataset_repository import DatasetRepository
from ...domain.repositories.rag_repository import RAGRepository
from ...domain.repositories.recording_repository import RecordingRepository
from ...domain.repositories.robot_repository import RobotRepository
from ...domain.repositories.sensor_data_repository import SensorDataRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.services.audit_service import AuditService
from ...domain.services.dataset_service import DatasetService
from ...domain.services.rag_service import RAGService
from ...domain.services.recording_service import RecordingService
from ...infrastructure.database.connection import get_session
from ...infrastructure.database.repositories.audit_repo import SQLAlchemyAuditRepository
from ...infrastructure.database.repositories.dataset_repo import SQLAlchemyDatasetRepository
from ...infrastructure.database.repositories.rag_repo import SQLAlchemyRAGRepository
from ...infrastructure.database.repositories.recording_repo import SQLAlchemyRecordingRepository
from ...infrastructure.database.repositories.robot_repo import SQLAlchemyRobotRepository
from ...infrastructure.database.repositories.sensor_data_repo import SQLAlchemySensorDataRepository
from ...infrastructure.database.repositories.user_repo import SQLAlchemyUserRepository

security = HTTPBearer(auto_error=False)


# ─── Database Session ────────────────────────────────────────────────────────


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Repositories ────────────────────────────────────────────────────────────


def get_user_repo(session: DbSession) -> UserRepository:
    return SQLAlchemyUserRepository(session)


def get_robot_repo(session: DbSession) -> RobotRepository:
    return SQLAlchemyRobotRepository(session)


def get_sensor_data_repo(session: DbSession) -> SensorDataRepository:
    return SQLAlchemySensorDataRepository(session)


def get_dataset_repo(session: DbSession) -> DatasetRepository:
    return SQLAlchemyDatasetRepository(session)


def get_rag_repo(session: DbSession) -> RAGRepository:
    return SQLAlchemyRAGRepository(session)


def get_audit_repo(session: DbSession) -> AuditRepository:
    return SQLAlchemyAuditRepository(session)


def get_recording_repo(session: DbSession) -> RecordingRepository:
    return SQLAlchemyRecordingRepository(session)


UserRepo = Annotated[UserRepository, Depends(get_user_repo)]
RobotRepo = Annotated[RobotRepository, Depends(get_robot_repo)]
SensorDataRepo = Annotated[SensorDataRepository, Depends(get_sensor_data_repo)]
DatasetRepo = Annotated[DatasetRepository, Depends(get_dataset_repo)]
RagRepo = Annotated[RAGRepository, Depends(get_rag_repo)]
AuditRepo = Annotated[AuditRepository, Depends(get_audit_repo)]
RecordingRepo = Annotated[RecordingRepository, Depends(get_recording_repo)]


# ─── Services ────────────────────────────────────────────────────────────────


def get_audit_service(repo: AuditRepo) -> AuditService:
    return AuditService(repo)


def get_dataset_service(
    dataset_repo: DatasetRepo,
    sensor_repo: SensorDataRepo,
) -> DatasetService:
    return DatasetService(dataset_repo, sensor_repo)


def get_recording_service(
    recording_repo: RecordingRepo,
    sensor_repo: SensorDataRepo,
) -> RecordingService:
    return RecordingService(recording_repo, sensor_repo)


AuditSvc = Annotated[AuditService, Depends(get_audit_service)]
DatasetSvc = Annotated[DatasetService, Depends(get_dataset_service)]
RecordingSvc = Annotated[RecordingService, Depends(get_recording_service)]


# ─── Authentication ──────────────────────────────────────────────────────────


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    user_repo: UserRepo,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, settings.jwt_public_key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await user_repo.get_by_id(UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ─── Authorization ───────────────────────────────────────────────────────────


def require_role(*roles: UserRole):
    """Dependency that checks the user has one of the required roles."""

    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user

    return checker


AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
OperatorUser = Annotated[
    User, Depends(require_role(UserRole.ADMIN, UserRole.OPERATOR))
]
