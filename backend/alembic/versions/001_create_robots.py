# =============================================================================
# Step 7: 初回マイグレーション — robots テーブルの作成
# =============================================================================
#
# 【マイグレーションファイルとは？】
# データベースのスキーマ変更を「差分」として記録するファイル。
# Git のコミットのように、DB の変更履歴を追跡できる。
#
# 各マイグレーションには:
#   - revision: このマイグレーションの一意な ID
#   - down_revision: 前のマイグレーション（None = 最初）
#   - upgrade(): 適用時に実行される処理
#   - downgrade(): 取り消し時に実行される処理
#
# 【実行コマンド】
#   alembic upgrade head       → 全マイグレーションを適用
#   alembic upgrade 001        → 特定のリビジョンまで適用
#   alembic downgrade -1       → 1つ戻す
#   alembic downgrade base     → 全部取り消し
#
# 【自動生成 vs 手動作成】
#   alembic revision --autogenerate -m "add users"
#   → ORM モデルと DB の差分を自動検出して生成
#
#   alembic revision -m "add custom index"
#   → 手動で upgrade/downgrade を書く
#
#   Step 7 では手動で作成して、中身を理解する。
#
# =============================================================================

"""robots テーブルの作成

Revision ID: 001
Revises: (なし — 最初のマイグレーション)
Create Date: 2024-01-01
"""

from alembic import op
import sqlalchemy as sa

# --- マイグレーション識別子 ---
revision = "001"
down_revision = None  # 最初のマイグレーションなので前バージョンはない
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    robots テーブルを作成する

    【op.create_table() とは？】
    Alembic の操作 API。
    内部的に `CREATE TABLE robots (...)` SQL を生成して実行する。

    各カラムの SQL 対応:
      sa.Column("id", sa.Uuid, primary_key=True)
        → id UUID PRIMARY KEY
      sa.Column("name", sa.String(100), unique=True, nullable=False)
        → name VARCHAR(100) UNIQUE NOT NULL
      sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
        → created_at TIMESTAMPTZ DEFAULT NOW()
    """
    op.create_table(
        "robots",
        # --- 主キー ---
        sa.Column("id", sa.Uuid, primary_key=True),

        # --- データカラム ---
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("robot_type", sa.String(50), nullable=False, server_default="differential"),
        sa.Column("description", sa.Text, nullable=True, server_default=""),
        sa.Column("status", sa.String(50), nullable=False, server_default="offline"),

        # --- タイムスタンプ ---
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- インデックスの作成 ---
    #
    # 【インデックスとは？】
    # DB が検索を高速化するためのデータ構造（B-Tree など）。
    # 本の索引のように、特定の値を持つ行をすばやく見つけられる。
    #
    # WHERE status = 'active' のようなクエリが頻繁にある場合、
    # status にインデックスを張ることで検索速度が大幅に向上する。
    #
    # ただし、INSERT/UPDATE 時にインデックスの更新コストがかかるため、
    # すべてのカラムにインデックスを張るのは逆効果。
    #
    op.create_index("ix_robots_name", "robots", ["name"], unique=True)
    op.create_index("ix_robots_status", "robots", ["status"])


def downgrade() -> None:
    """
    robots テーブルを削除する（upgrade の逆操作）

    【downgrade の重要性】
    問題が発生した場合にマイグレーションを取り消せるように、
    必ず逆操作を実装する。
    """
    op.drop_index("ix_robots_status", table_name="robots")
    op.drop_index("ix_robots_name", table_name="robots")
    op.drop_table("robots")
