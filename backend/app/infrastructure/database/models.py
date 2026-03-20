# =============================================================================
# Step 12: ORM モデル定義（RAG対応版）
# =============================================================================
#
# 【Step 11 からの変更点（Step 12）】
# RobotModel, UserModel, SensorDataModel, RecordingSessionModel, DatasetModel
# に加えて以下を追加:
# - RAGDocumentModel: RAG用ドキュメント（アップロードされた文書）
# - DocumentChunkModel: ドキュメントチャンク（文書を分割した断片 + ベクトル）
#
# 【各モデルの関係】
#
#   User ─────┬──── RecordingSession ──── SensorData
#             │           │
#             ├──── Dataset（RecordingSession のデータをまとめる）
#             │
#             └──── RAGDocument ──── DocumentChunk（ベクトル付き）
#
# 【pgvector とは？】
# PostgreSQL の拡張機能で、ベクトル（数値の配列）を効率的に保存・検索できる。
# 768次元のベクトル同士のコサイン類似度を高速に計算し、
# 意味的に近いテキストを見つけるのに使う。
#
# 通常の SQL:
#   SELECT * FROM products WHERE name = 'ロボット'  ← 完全一致検索
#
# pgvector:
#   SELECT * FROM chunks ORDER BY embedding <=> query_vector LIMIT 5
#   ← ベクトルが近い順（意味的に類似した順）に5件取得
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


# =============================================================================
# RAGDocumentModel（Step 12 新規）
# =============================================================================
#
# 【役割】
# アップロードされたドキュメント（PDF, TXT, MD ファイル）の情報を保存する。
# ドキュメント本体のテキストは chunks（チャンク）に分割して保存される。
#
# 【テーブルリレーション】
# RAGDocument ─── 1:N ──── DocumentChunk
# 1つのドキュメントが複数のチャンクに分割される。
#
class RAGDocumentModel(Base):
    """RAG ドキュメント（アップロードされた文書）"""
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(500), nullable=False,
    )
    # source: ファイル名やURLなど、ドキュメントの出所
    source: Mapped[str] = mapped_column(
        String(1000), nullable=False, default="",
    )
    # file_type: "pdf", "txt", "md" など
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="txt",
    )
    # content: ドキュメント全体のテキスト（チャンク分割の元データ）
    content: Mapped[str] = mapped_column(
        Text, nullable=False, default="",
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    # chunk_count: このドキュメントから生成されたチャンク数
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    # metadata_: ドキュメントの追加メタデータ（JSONB）
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default={},
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<RAGDocumentModel(id={self.id}, title='{self.title}')>"


# =============================================================================
# DocumentChunkModel（Step 12 新規）
# =============================================================================
#
# 【チャンク（Chunk）とは？】
# ドキュメントを小さな断片に分割したもの。
# 例: 10ページの PDF → 50個のチャンク（各チャンク: 500文字程度）
#
# 各チャンクには embedding（ベクトル埋め込み）が付与される:
# 「ロボットの安全機能について」→ [0.12, -0.45, 0.78, ..., 0.34]（768次元）
#
# 【なぜチャンクに分割するのか？】
# 1. LLM のコンテキストウィンドウに収まるサイズにする
# 2. 関連する部分だけを検索で取得できる（ドキュメント全体は不要）
# 3. ベクトル検索の精度が上がる（小さいテキストほど意味が明確）
#
# 【embedding カラム】
# pgvector の Vector 型を使用。768次元の浮動小数点配列を保存する。
# ※ ここでは Vector 型を使わず ARRAY(Float) で代用（pgvector拡張が不要な環境向け）
# 本番環境では pgvector の Vector(768) カラムと HNSW インデックスを使うのが推奨。
#
class DocumentChunkModel(Base):
    """ドキュメントチャンク（ベクトル埋め込み付き文書断片）"""
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    # 所属するドキュメントへの外部キー
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # チャンクのテキスト内容
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
    )
    # embedding: テキストをベクトルに変換したもの（768次元の浮動小数点配列）
    # 💡 pgvector の Vector(768) を使うのが理想だが、
    #    学習環境では ARRAY(Float) で代用する（pgvector 拡張不要）
    embedding: Mapped[list] = mapped_column(
        ARRAY(Float), nullable=True,
    )
    # chunk_index: ドキュメント内でのチャンクの順番（0始まり）
    chunk_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    # metadata_: チャンクの追加情報（ページ番号、セクション名など）
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default={},
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # ドキュメントIDで検索を高速化するインデックス
        Index("ix_chunks_document_id", "document_id"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunkModel(id={self.id}, doc={self.document_id}, idx={self.chunk_index})>"
