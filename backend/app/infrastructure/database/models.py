# =============================================================================
# Step 11: ORM モデル定義（データ記録対応版）
# =============================================================================
#
# 【Step 8 からの変更点（Step 11）】
# RobotModel, UserModel に加えて以下を追加:
# - SensorDataModel: センサーデータ（時系列データ）
# - RecordingSessionModel: 記録セッション（録画管理）
# - DatasetModel: 機械学習用データセット
#
# 【各モデルの関係】
#
#   User ─────┬──── RecordingSession ──── SensorData
#             │           │
#             └──── Dataset（RecordingSession のデータをまとめる）
#
# 【PostgreSQL 固有の型】
# - JSONB: JSON データを効率的に保存・検索できる PostgreSQL 固有の型
#   通常の JSON 型と違い、バイナリ形式で保存されるため検索が高速
# - ARRAY: PostgreSQL 配列型（[1, 2, 3] のようなリストを1カラムに保存）
#
# =============================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, DateTime, Uuid, Boolean,
    Integer, Text, Float, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from sqlalchemy import func


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


# =============================================================================
# SensorDataModel — sensor_data テーブル（Step 11 新規）
# =============================================================================
#
# 【テーブル設計のポイント】
#
# 1. timestamp に INDEX を設定
#    → 時系列データの検索はタイムスタンプが主キーになるため必須。
#    → 「過去1分間のデータ」「特定時間範囲のデータ」の取得が高速。
#
# 2. data カラムに JSONB 型を使用
#    → センサーの種類によってデータの構造が異なるため、
#      固定カラムではなく柔軟な JSONB を使う。
#    → 例: LiDAR → {"ranges": [0.5, 1.2, ...]}
#          IMU → {"accel_x": 0.1, "accel_y": 0.0, "accel_z": 9.8}
#
# 3. session_id は nullable
#    → 記録セッション中のデータのみ session_id を持つ。
#    → セッション外のリアルタイムデータは null。
#
# 4. 複合インデックス (robot_id, sensor_type, timestamp)
#    → 「このロボットのこのセンサーのこの時間範囲」の検索を高速化。
#
class SensorDataModel(Base):
    """センサーデータ ORM モデル"""
    __tablename__ = "sensor_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    sensor_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    # JSONB: センサーデータ本体（構造はセンサーごとに異なる）
    data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer, default=0,
    )

    __table_args__ = (
        Index("ix_sensor_data_robot_type_time", "robot_id", "sensor_type", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<SensorDataModel(id={self.id}, type='{self.sensor_type}')>"


# =============================================================================
# RecordingSessionModel — recording_sessions テーブル（Step 11 新規）
# =============================================================================
#
# 【RecordingSession（録画セッション）とは？】
# ユーザーが「記録開始」ボタンを押してから「記録停止」を押すまでの期間を
# 1つのセッションとして管理する。
#
# 【テーブル設計のポイント】
#
# 1. is_active: 現在録画中かどうか
#    → 1ロボットにつき同時に1セッションのみ active にする制約
# 2. config: JSONB で録画設定を柔軟に保存
#    → 対象センサー、最大周波数、フィルタ条件など
# 3. stopped_at: 録画中は NULL、停止したら日時が入る
# 4. dataset_id: 録画データをデータセットに変換した場合に設定
#
class RecordingSessionModel(Base):
    """録画セッション ORM モデル"""
    __tablename__ = "recording_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default={},
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True,
    )
    record_count: Mapped[int] = mapped_column(
        Integer, default=0,
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer, default=0,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
    )
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True,
    )

    __table_args__ = (
        Index("ix_recording_sessions_active", "robot_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<RecordingSessionModel(id={self.id}, active={self.is_active})>"


# =============================================================================
# DatasetModel — datasets テーブル（Step 11 新規）
# =============================================================================
#
# 【Dataset（データセット）とは？】
# 機械学習の学習に使うデータの集まり。
# 録画セッションのデータをまとめて、CSV/JSON にエクスポートできる。
#
# 【テーブル設計のポイント】
#
# 1. status: データセットのライフサイクルを管理
#    creating → ready → exporting → archived
# 2. sensor_types, robot_ids: ARRAY 型で複数の値をリスト保存
# 3. metadata: JSONB で追加情報を柔軟に保存
# 4. owner_id: データセットの所有者（ForeignKey で users テーブルを参照）
#
class DatasetModel(Base):
    """データセット ORM モデル"""
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text, default="",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="creating",
    )
    sensor_types: Mapped[list] = mapped_column(
        ARRAY(String), default=[],
    )
    robot_ids: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=[],
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    record_count: Mapped[int] = mapped_column(
        Integer, default=0,
    )
    size_bytes: Mapped[int] = mapped_column(
        Integer, default=0,
    )
    tags: Mapped[list] = mapped_column(
        ARRAY(String), default=[],
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default={},
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_datasets_owner", "owner_id"),
        Index("ix_datasets_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<DatasetModel(id={self.id}, name='{self.name}')>"
