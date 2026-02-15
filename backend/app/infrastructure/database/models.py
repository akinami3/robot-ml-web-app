# ============================================================
# SQLAlchemy ORM モデル定義
# （TimescaleDB + pgvector 対応）
# ============================================================
# データベースの各テーブルを Python のクラスとして定義するファイルです。
#
# 【ORM モデルとは？】
# ORM（Object-Relational Mapping）モデルは、
# データベースのテーブルを Python のクラスにマッピングします。
# 1つのクラス = 1つのテーブル、1つのインスタンス = 1つの行（レコード）。
#
# 【ドメインエンティティとの違い】
# - ドメインエンティティ（domain/entities/）: ビジネスロジック用
# - ORM モデル（このファイル）: データベース操作用
# 同じ「ユーザー」でも、用途によって別のクラスを使い分けます。
# これを「関心の分離」と呼びます。
#
# 【使用する PostgreSQL 拡張機能】
# 1. TimescaleDB: 時系列データの高速処理
#    - sensor_data テーブルを hypertable として定義
#    - time_bucket() 関数で時間単位の集計が高速
# 2. pgvector: ベクトル類似度検索
#    - document_chunks テーブルに 768次元のベクトルカラム
#    - HNSW インデックスで高速な近似最近傍検索
#
# 【mapped_column() の読み方】
# mapped_column(型, オプション...) でカラムを定義
# - primary_key=True: 主キー（行を一意に識別する）
# - nullable=False: NULL 値を許可しない
# - unique=True: 重複を許可しない
# - default=値: デフォルト値（Python 側で設定）
# - server_default=func.now(): デフォルト値（DB 側で設定）
# - index=True: インデックスを作成（検索高速化）
# ============================================================
"""SQLAlchemy ORM models with TimescaleDB and pgvector support."""

from __future__ import annotations

import uuid
from datetime import datetime

# pgvector: PostgreSQL のベクトル型をSQLAlchemyで使うための拡張
from pgvector.sqlalchemy import Vector
# SQLAlchemy のカラム型定義
from sqlalchemy import (
    Boolean,     # 真偽値型（True/False）
    DateTime,    # 日時型
    Enum,        # 列挙型（固定された選択肢）
    Float,       # 浮動小数点数型
    ForeignKey,  # 外部キー（他のテーブルへの参照）
    Index,       # インデックス（検索高速化）
    Integer,     # 整数型
    String,      # 文字列型（最大長指定）
    Text,        # テキスト型（長さ無制限）
    func,        # SQL関数（NOW() 等）
)
# PostgreSQL 固有の型
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
# Mapped: 型アノテーション付きのカラム定義
# mapped_column: カラムの詳細設定
# relationship: テーブル間のリレーション（関連）定義
from sqlalchemy.orm import Mapped, mapped_column, relationship

# ドメインエンティティの列挙型（テーブルのカラムに使用）
from ...domain.entities.audit_log import AuditAction
from ...domain.entities.dataset import DatasetStatus
from ...domain.entities.robot import RobotState
from ...domain.entities.sensor_data import SensorType
from ...domain.entities.user import UserRole
# ORM の基底クラス（connection.py で定義）
from .connection import Base


# ─────────────────────────────────────────────────────────────
# ユーザーテーブル（Users）
# ─────────────────────────────────────────────────────────────
# アプリケーションのユーザー情報を保存するテーブル。
# ユーザー名とメールアドレスは一意（unique）制約付き。
# ─────────────────────────────────────────────────────────────

class UserModel(Base):
    """ユーザーテーブルの ORM モデル。"""

    # __tablename__: この Python クラスが対応するテーブル名
    __tablename__ = "users"

    # ── 主キー（Primary Key）──
    # UUID を主キーとして使用。自動生成される一意の識別子。
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── ユーザー情報カラム ──
    # String(100): 最大100文字の文字列型
    # unique=True: 同じ値を持つレコードは作れない
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # ハッシュ化されたパスワード（元のパスワードは保存しない！）
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── ロール（権限レベル）──
    # Enum 型: UserRole の値のみ許可（admin, operator, viewer）
    role: Mapped[str] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.VIEWER,  # デフォルトは閲覧者
    )
    # アカウントが有効かどうか（論理削除に使用）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── タイムスタンプ ──
    # server_default=func.now(): DB サーバー側で現在時刻を設定
    # onupdate=func.now(): レコード更新時に自動的に現在時刻に更新
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── リレーションシップ（テーブル間の関連） ──
    # relationship(): 他のテーブルとの関連を定義
    # back_populates: 双方向の関連（DatasetModel.owner ↔ UserModel.datasets）
    # lazy="selectin": 関連データを SELECT IN で効率的に読み込む
    # lazy="noload": 関連データを自動的には読み込まない（必要な時だけ）
    datasets = relationship("DatasetModel", back_populates="owner", lazy="selectin")
    audit_logs = relationship("AuditLogModel", back_populates="user", lazy="noload")


# ─────────────────────────────────────────────────────────────
# ロボットテーブル（Robots）
# ─────────────────────────────────────────────────────────────
# 管理対象のロボット情報を保存するテーブル。
# 接続パラメータは JSONB 型で柔軟に保存。
# ─────────────────────────────────────────────────────────────

class RobotModel(Base):
    """ロボットテーブルの ORM モデル。"""
    __tablename__ = "robots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # ロボット名（ユニーク制約付き）
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    # アダプタータイプ（通信方式: "ros2", "mock" 等）
    adapter_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # ロボットの状態（Enum 型で制限）
    state: Mapped[str] = mapped_column(
        Enum(RobotState, name="robot_state", create_constraint=True),
        default=RobotState.DISCONNECTED,
    )

    # ── PostgreSQL 固有の型 ──
    # ARRAY(String): 文字列の配列型（例: ["navigation", "manipulation"]）
    capabilities: Mapped[list] = mapped_column(ARRAY(String), default=[])
    # JSONB: JSON バイナリ型（構造化されたデータを柔軟に保存）
    # JSONBのメリット: インデックスが効く、部分的な検索が可能
    connection_params: Mapped[dict] = mapped_column(JSONB, default={})

    # バッテリー残量（0.0〜100.0）、nullable=True で NULL 許可
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    # 最後にデータを受信した時刻
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── テーブル引数 ──
    # __table_args__: テーブルレベルの設定（インデックス等）
    # Index("名前", "カラム名"): 指定カラムにインデックスを作成
    __table_args__ = (Index("ix_robots_state", "state"),)


# ─────────────────────────────────────────────────────────────
# センサーデータテーブル（Sensor Data）
# TimescaleDB ハイパーテーブル
# ─────────────────────────────────────────────────────────────
# 時系列のセンサーデータを保存するテーブル。
#
# 【TimescaleDB ハイパーテーブル】
# 通常のテーブルを時間軸で自動分割（チャンク化）する機能。
# 大量の時系列データでも検索・挿入が高速。
# __table_args__ の timescaledb_hypertable で設定。
# ─────────────────────────────────────────────────────────────

class SensorDataModel(Base):
    """センサーデータテーブルの ORM モデル（TimescaleDB ハイパーテーブル）。"""
    __tablename__ = "sensor_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # タイムスタンプ（時系列データの最重要カラム）
    # index=True: 時間での検索を高速化
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # どのロボットのデータか
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # センサーの種類（LiDAR, IMU, カメラ等）
    sensor_type: Mapped[str] = mapped_column(
        Enum(SensorType, name="sensor_type", create_constraint=True), nullable=False
    )
    # センサーデータの本体（JSONB 型で柔軟に保存）
    # 例: {"x": 1.5, "y": 2.3, "z": 0.1} や {"image_base64": "..."}
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # 録画セッションID（録画中のデータのみ設定される）
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    # データの順序を保証するシーケンス番号
    sequence_number: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        # 複合インデックス: robot_id + sensor_type + timestamp の組み合わせで高速検索
        # 「このロボットの、このセンサーの、この時間範囲のデータ」を素早く取得
        Index("ix_sensor_data_robot_type_time", "robot_id", "sensor_type", "timestamp"),
        # TimescaleDB ハイパーテーブルの設定
        # timestamp カラムを基準にデータを自動的にチャンク分割する
        {"timescaledb_hypertable": {"time_column_name": "timestamp"}},
    )


# ─────────────────────────────────────────────────────────────
# データセットテーブル（Datasets）
# ─────────────────────────────────────────────────────────────
# 機械学習用のデータセット情報を保存するテーブル。
# 実データはセンサーデータテーブルにあり、
# ここはメタデータ（名前、説明、対象ロボット等）を保存。
# ─────────────────────────────────────────────────────────────

class DatasetModel(Base):
    """データセットテーブルの ORM モデル。"""
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")

    # 外部キー: users テーブルの id を参照
    # ForeignKey("テーブル名.カラム名"): 参照先を指定
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # データセットのステータス（作成中/準備完了/エクスポート中）
    status: Mapped[str] = mapped_column(
        Enum(DatasetStatus, name="dataset_status", create_constraint=True),
        default=DatasetStatus.CREATING,
    )

    # ARRAY 型: PostgreSQL の配列型
    # 例: ["lidar", "imu", "camera"] や [UUID1, UUID2]
    sensor_types: Mapped[list] = mapped_column(ARRAY(String), default=[])
    robot_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=[])

    # データ収集の時間範囲（省略可能なため nullable=True）
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 統計情報
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # タグ（分類用ラベル）
    tags: Mapped[list] = mapped_column(ARRAY(String), default=[])
    # メタデータ（追加情報、JSONB で柔軟に保存）
    # 「metadata_」と末尾に _ が付いているのは、Python の組み込み名との衝突を避けるため
    # "metadata" はDB上のカラム名
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # リレーション: このデータセットの所有者（UserModel）
    owner = relationship("UserModel", back_populates="datasets")

    __table_args__ = (
        Index("ix_datasets_owner", "owner_id"),   # 所有者での検索用
        Index("ix_datasets_status", "status"),     # ステータスでの検索用
    )


# ─────────────────────────────────────────────────────────────
# RAG ドキュメントテーブル（RAG Documents）
# ─────────────────────────────────────────────────────────────
# アップロードされた文書の情報を保存するテーブル。
# テキスト内容のプレビュー（先頭1000文字）を保存。
# 実際のチャンク（断片）は document_chunks テーブルに保存。
# ─────────────────────────────────────────────────────────────

class RAGDocumentModel(Base):
    """RAG ドキュメントテーブルの ORM モデル。"""
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")  # プレビュー用
    source: Mapped[str] = mapped_column(String(1000), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    file_type: Mapped[str] = mapped_column(String(50), default="text")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # リレーション: このドキュメントに属するチャンク
    # cascade="all, delete-orphan": 親（ドキュメント）削除時に子（チャンク）も自動削除
    chunks = relationship(
        "DocumentChunkModel", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_rag_documents_owner", "owner_id"),)


# ─────────────────────────────────────────────────────────────
# ドキュメントチャンクテーブル（Document Chunks）
# pgvector によるベクトル類似度検索対応
# ─────────────────────────────────────────────────────────────
# ドキュメントを分割した個々のチャンク（断片）を保存。
# 各チャンクに 768次元のベクトル埋め込みを持つ。
#
# 【HNSW インデックスとは？】
# Hierarchical Navigable Small World の略。
# ベクトル間の近似最近傍検索を高速に行うためのインデックス。
# 完全一致検索ではなく「近似」検索のため、速度と精度のトレードオフがある。
# m=16: グラフの接続数（多いほど精度↑、メモリ↑）
# ef_construction=64: 構築時の探索幅（多いほど精度↑、構築時間↑）
# ─────────────────────────────────────────────────────────────

class DocumentChunkModel(Base):
    """ドキュメントチャンクテーブルの ORM モデル（pgvector 対応）。"""
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 親ドキュメントへの外部キー
    # ondelete="CASCADE": 親ドキュメント削除時にこのチャンクも自動削除（DB レベル）
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    # チャンクのテキスト内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # ベクトル埋め込み（768次元の浮動小数点数配列）
    # Vector(768): pgvector の 768次元ベクトル型
    # nomic-embed-text モデルが出力する次元数に合わせている
    embedding = mapped_column(Vector(768), nullable=True)
    # チャンクの順番（0始まり）
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    # おおよそのトークン数
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # リレーション: このチャンクが属するドキュメント
    document = relationship("RAGDocumentModel", back_populates="chunks")

    __table_args__ = (
        # ドキュメントIDでの検索用インデックス
        Index("ix_document_chunks_document", "document_id"),
        # HNSW ベクトルインデックス（pgvector）
        # ベクトル類似度検索を高速化する特殊なインデックス
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",                         # HNSW アルゴリズムを使用
            postgresql_with={"m": 16, "ef_construction": 64}, # インデックスパラメータ
            postgresql_ops={"embedding": "vector_cosine_ops"}, # コサイン類似度で検索
        ),
    )


# ─────────────────────────────────────────────────────────────
# 録画セッションテーブル（Recording Sessions）
# ─────────────────────────────────────────────────────────────
# センサーデータの録画セッション情報を保存するテーブル。
# 録画の開始/停止時刻、設定、統計情報を管理。
# ─────────────────────────────────────────────────────────────

class RecordingSessionModel(Base):
    """録画セッションテーブルの ORM モデル。"""
    __tablename__ = "recording_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 録画対象のロボットID
    robot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # 録画を開始したユーザーのID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # 録画設定（JSONB: 対象センサータイプ、最大周波数等）
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default={})
    # 録画中かどうか（True: 録画中、False: 停止済み）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # 記録されたデータの件数
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    # データサイズ（バイト）
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    # 録画開始時刻
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # 録画停止時刻（録画中は NULL）
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 関連するデータセットのID（データセットに変換した場合に設定）
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=True
    )

    __table_args__ = (
        # 複合インデックス: ロボットID + アクティブ状態
        # 「このロボットで現在録画中のセッション」を高速に検索
        Index("ix_recording_sessions_active", "robot_id", "is_active"),
    )


# ─────────────────────────────────────────────────────────────
# 監査ログテーブル（Audit Logs）
# ─────────────────────────────────────────────────────────────
# ユーザーの操作履歴（誰が・いつ・何をしたか）を記録するテーブル。
# セキュリティ監査やトラブルシューティングに使用。
# ─────────────────────────────────────────────────────────────

class AuditLogModel(Base):
    """監査ログテーブルの ORM モデル。"""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 操作を行ったユーザーのID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # 操作の種類（LOGIN_SUCCESS, ROBOT_CREATE 等）
    action: Mapped[str] = mapped_column(
        Enum(AuditAction, name="audit_action", create_constraint=True), nullable=False
    )
    # 操作対象のリソース種別と ID
    resource_type: Mapped[str] = mapped_column(String(100), default="")
    resource_id: Mapped[str] = mapped_column(String(255), default="")
    # 操作の詳細情報（JSONB で柔軟に保存）
    details: Mapped[dict] = mapped_column(JSONB, default={})
    # 操作元の情報（セキュリティ追跡用）
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(String(500), default="")
    # 操作日時
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # リレーション: 操作を行ったユーザー
    user = relationship("UserModel", back_populates="audit_logs")

    __table_args__ = (
        # 複合インデックス: ユーザーID + 日時（ユーザーの操作履歴検索用）
        Index("ix_audit_logs_user_time", "user_id", "timestamp"),
        # 操作種別でのインデックス
        Index("ix_audit_logs_action", "action"),
        # リソースでのインデックス（特定リソースの操作履歴検索用）
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
