# =============================================================================
# Step 7: SQLAlchemy ORM モデル — データベーステーブルの定義
# =============================================================================
#
# 【ORM モデルとは？】
# Python クラスと DB テーブルの対応付け（マッピング）を定義するもの。
#
# RobotModel クラス = robots テーブル
#   robot.name      → robots.name カラム
#   robot.status    → robots.status カラム
#   robot.id        → robots.id カラム（主キー）
#
# 【ドメインエンティティと ORM モデルの違い】
#
#   ドメインエンティティ (domain/entities/robot.py):
#     - ビジネスロジック用
#     - DB に依存しない（dataclass）
#     - テスト時に DB なしで使える
#
#   ORM モデル (このファイル):
#     - DB テーブルの構造を定義
#     - SQLAlchemy に依存
#     - マイグレーションの源泉
#
# なぜ2つ存在する？
#   → 関心の分離。DB 構造の変更がビジネスロジックに波及しないようにする。
#     小規模プロジェクトでは1つにまとめることもあるが、
#     学習のために分離する（Clean Architecture を理解するため）。
#
# 【Mapped / mapped_column とは？】
# SQLAlchemy 2.0 の新しい書き方。
# 型アノテーションでカラムの型を宣言する（従来の Column() より型安全）。
#
#   旧: name = Column(String(100), nullable=False)
#   新: name: Mapped[str] = mapped_column(String(100))
#
# =============================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, Uuid
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


# =============================================================================
# ベースモデル
# =============================================================================
#
# 【DeclarativeBase とは？】
# SQLAlchemy 2.0 でモデルクラスの基底クラスとして使用する。
# 旧バージョンの `declarative_base()` に相当。
#
# 全 ORM モデルはこのクラスを継承する。
# SQLAlchemy はこのクラスのサブクラスを自動的にテーブルとして認識する。
#
class Base(DeclarativeBase):
    pass


# =============================================================================
# RobotModel — robots テーブル
# =============================================================================
#
# 【__tablename__ とは？】
# DB 上のテーブル名。クラス名とは別に明示的に指定する。
# 命名規則: 小文字、複数形（robots, users, sensor_data）
#
# 【UUID 主キー】
# 自動インクリメント (1, 2, 3...) ではなく UUID (ランダム) を使う理由:
#   1. 分散システムで ID が衝突しない
#   2. ID から総レコード数が推測できない（セキュリティ）
#   3. DB を分割（シャーディング）してもユニーク性が保たれる
#
# デメリット:
#   - 自動インクリメントより少しだけ遅い
#   - 文字列で扱うとインデックスが大きくなる
#   → PostgreSQL の UUID 型を使えば16バイトで効率的
#
class RobotModel(Base):
    """
    ロボット ORM モデル

    DB テーブル `robots` にマッピングされる。
    """
    __tablename__ = "robots"

    # --- 主キー ---
    # server_default=... ではなく Python 側で uuid4() を生成。
    # default= は INSERT 時に Python が値を設定する。
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    # --- ロボットデータ ---
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,       # 同じ名前のロボットは登録不可
        index=True,        # 名前で検索するためインデックスを張る
    )

    robot_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="differential",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="offline",
        index=True,        # ステータスで絞り込むことが多い
    )

    # --- タイムスタンプ ---
    #
    # 【timezone.utc の重要性】
    # DB には常に UTC で保存し、表示時にローカルタイムゾーンに変換する。
    # タイムゾーンの混在はバグの温床。"常に UTC" が鉄則。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<RobotModel(id={self.id}, name='{self.name}', status='{self.status}')>"
