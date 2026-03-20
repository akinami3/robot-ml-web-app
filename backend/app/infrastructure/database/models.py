# =============================================================================
# Step 8: UserModel — users テーブルの ORM 定義
# =============================================================================
#
# 【Step 7 からの変更点】
# RobotModel に加えて、UserModel を追加する。
# Base クラスは Step 7 と同じものを共有する。
#
# 【セキュリティに関わるカラム設計】
# - hashed_password: bcrypt ハッシュ（平文パスワードは絶対に保存しない）
# - is_active: アカウント無効化フラグ（削除ではなく無効化 = ソフトデリート）
# - role: RBAC のロール（権限レベル）
#
# =============================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Uuid, Boolean
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


# =============================================================================
# ベースモデル（Step 7 と同一）
# =============================================================================
class Base(DeclarativeBase):
    pass


# =============================================================================
# RobotModel（Step 7 と同一）
# =============================================================================
class RobotModel(Base):
    """ロボット ORM モデル"""
    __tablename__ = "robots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
    )
    robot_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="differential",
    )
    description: Mapped[str] = mapped_column(
        String(500), nullable=False, default="",
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="offline", index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<RobotModel(id={self.id}, name='{self.name}')>"


# =============================================================================
# UserModel — users テーブル（Step 8 新規）
# =============================================================================
#
# 【テーブル設計のポイント】
#
# 1. username は UNIQUE + INDEX
#    → ログイン時に username で検索するため、インデックスが必須。
#    → 同じ username の重複登録を DB 側で防止。
#
# 2. email も UNIQUE + INDEX
#    → パスワードリセットなどで email 検索が必要。
#
# 3. hashed_password は String(255)
#    → bcrypt ハッシュは約60文字だが、余裕を持たせる。
#    → 将来 argon2 に移行した場合、もう少し長くなる可能性がある。
#
# 4. role は String(50)
#    → Enum 型を DB に使うこともできるが、
#      マイグレーションの柔軟性のため String にする。
#
class UserModel(Base):
    """ユーザー ORM モデル"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )

    # --- 認証情報 ---
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # --- 権限・状態 ---
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="viewer",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # --- タイムスタンプ ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username='{self.username}', role='{self.role}')>"
