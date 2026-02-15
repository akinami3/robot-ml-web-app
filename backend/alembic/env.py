"""
=============================================================================
Alembic 環境設定ファイル（env.py）
=============================================================================

【Alembic（アレンビック）とは？】
データベースの「マイグレーション」を管理するツールです。

【マイグレーションとは？】
データベースのテーブル構造（スキーマ）の変更を、バージョン管理する仕組みです。
Gitがソースコードの変更履歴を管理するように、
Alembicはデータベースの変更履歴を管理します。

例:
  バージョン1: users テーブルを作成（id, name, email）
  バージョン2: users テーブルに age カラムを追加
  バージョン3: robots テーブルを新規作成

【なぜマイグレーションが必要？】
1. チーム開発: 全員のDBスキーマを同じ状態に保てる
2. 本番環境: 安全にスキーマを変更できる（ロールバックも可能）
3. 履歴管理: いつ、何を変更したかが記録される

【このファイルの役割】
Alembicがマイグレーションを実行する際の環境設定を行います。
- どのデータベースに接続するか
- どのテーブル定義（モデル）を参照するか
- オフライン/オンラインどちらのモードで実行するか

【async対応について】
このプロジェクトではSQLAlchemyを非同期（async）モードで使用しているため、
Alembicも非同期対応の設定になっています。
=============================================================================
"""

# 【asyncio】Pythonの非同期処理ライブラリ
# 非同期（async）でのデータベース接続に必要
import asyncio

# 【fileConfig】Pythonの標準ログ設定ツール
# Alembicの設定ファイル（alembic.ini）からログ設定を読み込みます
from logging.config import fileConfig

# 【context】Alembicのマイグレーション実行コンテキスト
# マイグレーションの設定や実行を管理するオブジェクト
from alembic import context

# 【pool】SQLAlchemyのコネクションプール設定
# NullPool: コネクションをプールしない（マイグレーション用）
from sqlalchemy import pool

# 【async_engine_from_config】非同期対応のSQLAlchemyエンジンを設定から作成
# エンジン = データベースへの接続を管理するオブジェクト
from sqlalchemy.ext.asyncio import async_engine_from_config

# 【get_settings】アプリケーションの設定を取得
# データベースURLなどの接続情報が含まれます
from app.config import get_settings

# 【Base】SQLAlchemyの宣言的ベースクラス
# すべてのテーブル定義（モデル）はこのBaseを継承しています
# Base.metadata にすべてのテーブルの構造情報が格納されている
from app.infrastructure.database.connection import Base

# 【モデルのインポート】
# noqa: F401, F403 → リンターの警告を抑制
# 直接使用しなくても、import することで Base.metadata にテーブル情報が登録される
# これがないと、Alembicはどのテーブルが存在するか分からない
from app.infrastructure.database.models import *  # noqa: F401, F403

# 【config】Alembicの設定オブジェクト（alembic.iniの内容）
# データベースURL、ログ設定、マイグレーションディレクトリなどを含む
config = context.config

# 【ログ設定】alembic.ini に定義されたログ設定を適用
# マイグレーション実行時のログ出力レベルやフォーマットを設定する
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 【target_metadata】Alembicが参照するメタデータ
# Base.metadata にはすべてのSQLAlchemyモデルのテーブル構造が含まれる
# Alembicはこのメタデータと実際のDBスキーマを比較して、
# 差分（何を変更すべきか）を自動検出する（autogenerate機能）
target_metadata = Base.metadata


def get_url() -> str:
    """
    データベースの接続URLを取得します。

    【接続URLの形式】
    dialect+driver://username:password@host:port/database
    例: postgresql+asyncpg://user:pass@localhost:5432/mydb
        sqlite+aiosqlite:///path/to/db.sqlite
    """
    settings = get_settings()
    return settings.database_url


def run_migrations_offline() -> None:
    """
    オフラインモードでマイグレーションを実行します。

    【オフラインモードとは？】
    実際にデータベースに接続せずに、SQLスクリプトだけを生成するモード。

    【使いどころ】
    - データベースに直接アクセスできない環境（本番環境のセキュリティ制限など）
    - DBA（データベース管理者）がSQLを確認してから手動で適用したい場合
    - マイグレーションのSQL文を事前に確認・レビューしたい場合

    生成されるSQLの例:
      ALTER TABLE users ADD COLUMN age INTEGER;
      CREATE INDEX ix_users_email ON users (email);
    """
    url = get_url()
    context.configure(
        url=url,                              # データベースURL
        target_metadata=target_metadata,       # テーブル構造の参照
        literal_binds=True,                    # パラメータをSQL文に直接埋め込む
        dialect_opts={"paramstyle": "named"},   # 名前付きパラメータスタイル
    )

    # 【begin_transaction】トランザクション内でマイグレーションを実行
    # トランザクション: 一連の操作をまとめて実行し、途中でエラーがあれば全て巻き戻す
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """
    実際のマイグレーション実行処理。

    【connection】データベースへの接続オブジェクト
    この関数は run_sync 経由で呼ばれ、非同期接続を同期的に使用します。
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    非同期（async）でマイグレーションを実行します。

    【非同期マイグレーションの仕組み】
    1. 非同期エンジン（async engine）を作成
    2. 非同期接続（async connection）を取得
    3. run_sync で同期的にマイグレーションを実行
       → Alembicのマイグレーション処理自体は同期的なため、
         run_sync で非同期接続上で同期処理を実行する

    【NullPool を使う理由】
    マイグレーションは一度実行したら終わりの短命な処理。
    コネクションプール（接続の使い回し）は不要なため、
    NullPool を指定して接続を即座に解放します。
    """
    # 【設定の取得と上書き】
    # alembic.ini の設定セクションを取得し、データベースURLを上書き
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    # 【非同期エンジンの作成】
    # async_engine_from_config: 設定辞書から非同期SQLAlchemyエンジンを作成
    #   prefix="sqlalchemy.": 設定キーのプレフィックス
    #   poolclass=pool.NullPool: コネクションプールを無効化
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # 【非同期コンテキストマネージャ】
    # async with で接続を取得、ブロック終了時に自動で接続を閉じる
    async with connectable.connect() as connection:
        # 【run_sync】非同期接続上で同期関数を実行
        # do_run_migrations は同期関数だが、非同期接続を使って実行される
        await connection.run_sync(do_run_migrations)

    # 【エンジンの破棄】接続リソースをクリーンアップ
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    オンラインモードでマイグレーションを実行します。

    【オンラインモードとは？】
    データベースに直接接続して、リアルタイムでマイグレーションを適用するモード。
    通常の開発時や自動デプロイで使用します。

    【asyncio.run()】
    非同期関数を同期的に実行するためのエントリーポイント。
    新しいイベントループを作成し、非同期関数が完了するまで待機します。
    """
    asyncio.run(run_async_migrations())


# 【メインの実行分岐】
# Alembicの実行モード（オフライン/オンライン）に応じて処理を分岐
# オフラインモード: alembic upgrade head --sql のように --sql フラグ付きで実行
# オンラインモード: alembic upgrade head のように通常実行
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
