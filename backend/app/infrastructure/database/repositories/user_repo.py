# =============================================================================
# Step 8: SQLAlchemy ユーザーリポジトリ実装
# =============================================================================
#
# RobotRepository と同じパターンで実装する。
# エンティティ ↔ ORM モデルの変換 + CRUD + 認証固有の検索。
#
# =============================================================================

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repo import UserRepository
from app.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy によるユーザーリポジトリの実装"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # =========================================================================
    # エンティティ ↔ ORM 変換
    # =========================================================================

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """ORM モデル → ドメインエンティティ"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            role=UserRole(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        """ドメインエンティティ → ORM モデル"""
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            role=entity.role.value,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # =========================================================================
    # CRUD
    # =========================================================================

    async def get_by_id(self, entity_id: UUID) -> User | None:
        model = await self._session.get(UserModel, entity_id)
        return self._to_entity(model) if model else None

    async def list_all(self) -> list[User]:
        stmt = select(UserModel).order_by(UserModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create(self, entity: User) -> User:
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, entity: User) -> User:
        model = await self._session.get(UserModel, entity.id)
        if model is None:
            msg = f"User not found: {entity.id}"
            raise ValueError(msg)

        model.username = entity.username
        model.email = entity.email
        model.hashed_password = entity.hashed_password
        model.role = entity.role.value
        model.is_active = entity.is_active
        model.updated_at = datetime.now(timezone.utc)

        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: UUID) -> bool:
        model = await self._session.get(UserModel, entity_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.commit()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(UserModel)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # 認証固有メソッド
    # =========================================================================

    async def find_by_username(self, username: str) -> User | None:
        """ユーザー名で検索（ログイン認証に使用）"""
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_entity(model) if model else None

    async def find_by_email(self, email: str) -> User | None:
        """メールアドレスで検索（重複チェックに使用）"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        return self._to_entity(model) if model else None
