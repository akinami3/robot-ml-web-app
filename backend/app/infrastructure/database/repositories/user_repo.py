"""SQLAlchemy implementation of UserRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import User, UserRole
from ....domain.repositories.user_repository import UserRepository
from ..models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            role=UserRole(model.role) if isinstance(model.role, str) else model.role,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            role=entity.role,
            is_active=entity.is_active,
        )

    async def get_by_id(self, id: UUID) -> User | None:
        result = await self._session.get(UserModel, id)
        return self._to_entity(result) if result else None

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[User]:
        stmt = select(UserModel).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: User) -> User:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, entity: User) -> User:
        model = await self._session.get(UserModel, entity.id)
        if model is None:
            raise ValueError(f"User {entity.id} not found")
        model.username = entity.username
        model.email = entity.email
        model.role = entity.role
        model.is_active = entity.is_active
        if entity.hashed_password:
            model.hashed_password = entity.hashed_password
        await self._session.flush()
        return self._to_entity(model)

    async def delete(self, id: UUID) -> bool:
        model = await self._session.get(UserModel, id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def count(self) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(UserModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_active_users(self) -> list[User]:
        stmt = select(UserModel).where(UserModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]
