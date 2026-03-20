# =============================================================================
# Step 7: Alembic 環境設定（env.py）
# =============================================================================
#
# 【このファイルの役割】
# Alembic がマイグレーションを実行するときに呼ばれるスクリプト。
# DB 接続の設定と、マイグレーションの実行方法を定義する。
#
# 【重要なポイント】
# Alembic は「同期」で動作するため、asyncpg ではなく psycopg2 を使う。
# config.py の DATABASE_URL_SYNC を参照する。
#
# target_metadata に ORM の Base.metadata を設定することで、
# `alembic revision --autogenerate` が ORM モデルとの差分を検出できる。
#
# =============================================================================

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# --- ORM モデルの metadata をインポート ---
# これにより Alembic が RobotModel などのテーブル定義を認識する。
# --autogenerate で「モデルと DB の差分」を検出するために必要。
from app.infrastructure.database.models import Base
from app.config import settings

# --- Alembic の設定オブジェクト ---
config = context.config

# --- DB URL を Python コードから設定 ---
# alembic.ini のダミー URL を、config.py の実際の URL で上書きする。
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

# --- ロギング設定 ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- メタデータの設定 ---
# Alembic が知っているテーブル定義。
# autogenerate でモデルの変更を検出するために必要。
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    オフラインモード: SQL スクリプトを生成するだけで DB に接続しない。
    `alembic upgrade head --sql` で使用される。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    オンラインモード: 実際に DB に接続してマイグレーションを実行。
    通常の `alembic upgrade head` で使用される。

    【engine_from_config とは？】
    alembic.ini の設定からエンジンを生成する。
    poolclass=pool.NullPool でコネクションプールを無効化。
    マイグレーションは一回きりの操作なのでプールは不要。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
