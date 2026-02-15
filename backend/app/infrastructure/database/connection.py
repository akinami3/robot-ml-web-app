# ============================================================
# データベース接続管理（Database Connection Management）
# ============================================================
# PostgreSQL データベースへの非同期接続を管理するモジュールです。
#
# 【使用技術】
# - SQLAlchemy 2.0: Python の代表的な ORM（Object-Relational Mapping）
# - asyncpg: PostgreSQL 用の高速な非同期ドライバ
#
# 【非同期（async）とは？】
# データベースの応答を待つ間、他のリクエストを処理できる仕組み。
# 同期処理だと1つのDB問い合わせが完了するまで何もできないが、
# 非同期処理なら待ち時間を有効活用できる。
#
# 【接続プールとは？】
# データベース接続を予め複数作っておいて使い回す仕組み。
# 毎回新しい接続を作るのは時間がかかるため、
# プールから「借りて」使い、終わったら「返す」方式で高速化する。
#
# 【セッション（Session）とは？】
# データベースとの「会話」の単位。1つのリクエスト処理中に
# 行った変更をまとめて確定（commit）または取消（rollback）する。
# ============================================================
"""Database connection management."""

from __future__ import annotations

# AsyncGenerator: 非同期ジェネレータの型ヒント（yield を使う非同期関数の戻り値型）
from typing import AsyncGenerator

# SQLAlchemy の非同期関連クラスをインポート
from sqlalchemy.ext.asyncio import (
    AsyncEngine,          # 非同期データベースエンジン（接続プールを管理）
    AsyncSession,         # 非同期セッション（DBとの会話の単位）
    async_sessionmaker,   # セッションを作るファクトリ（工場）
    create_async_engine,  # エンジンを作る関数
)
# DeclarativeBase: ORM モデルの基底クラス（全テーブルの親）
from sqlalchemy.orm import DeclarativeBase

# アプリケーション設定（データベースURL等）を取得
from ...config import Settings


class Base(DeclarativeBase):
    """
    全ての ORM モデルの基底クラス。

    【ORM（Object-Relational Mapping）とは？】
    データベースのテーブルを Python のクラスとして扱う仕組み。
    SQL を直接書かなくても、Python のコードでデータベース操作ができる。

    例: UserModel クラスが users テーブルに対応
    """
    pass


# モジュールレベルの変数（グローバル変数）
# アプリケーション起動時に一度だけ初期化され、全リクエストで共有される
_engine: AsyncEngine | None = None             # データベースエンジン
_session_factory: async_sessionmaker[AsyncSession] | None = None  # セッション工場


async def init_db(settings: Settings) -> None:
    """
    データベースエンジンとセッションファクトリを初期化する。

    【アプリケーション起動時に1回だけ呼ばれる】
    main.py の lifespan 関数から呼び出される。

    Args:
        settings: アプリケーション設定（DB接続URL、プールサイズ等）
    """
    # global キーワード: モジュールレベルの変数を関数内で変更するために必要
    global _engine, _session_factory

    # データベースエンジン（接続プール）を作成
    _engine = create_async_engine(
        settings.database_url,         # DB接続URL（例: postgresql+asyncpg://user:pass@host/db）
        echo=settings.debug,           # True にすると SQL クエリをログに出力（開発時に便利）
        pool_size=settings.db_pool_size,       # プール内の接続数（デフォルト: 10）
        max_overflow=settings.db_max_overflow, # プールが満杯の時に追加で作れる接続数
        pool_pre_ping=True,            # 使用前に接続が生きているか確認（切断対策）
        pool_recycle=3600,             # 1時間（3600秒）で接続を作り直す（古い接続対策）
    )

    # セッションファクトリ（セッションを量産する工場）を作成
    _session_factory = async_sessionmaker(
        bind=_engine,                  # このエンジンに紐づくセッションを作る
        class_=AsyncSession,           # 非同期セッションクラスを使用
        expire_on_commit=False,        # commit 後もオブジェクトの属性にアクセス可能にする
    )


async def close_db() -> None:
    """
    データベースエンジンを閉じる（全接続を解放）。

    【アプリケーション終了時に1回だけ呼ばれる】
    main.py の lifespan 関数の finally ブロックから呼び出される。
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()  # 全接続を閉じてリソースを解放
        _engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    データベースセッションを提供する依存性注入（DI）関数。

    【FastAPI の Depends() で使用】
    各リクエストハンドラが自動的にセッションを受け取れる。

    【yield を使ったコンテキスト管理】
    yield の前: セッションを作成して提供
    yield: エンドポイントの処理が実行される
    yield の後: 成功時は commit、エラー時は rollback

    【トランザクション管理】
    try/except でエラーが起きた場合は自動的に rollback する。
    これにより、途中でエラーが起きても
    データベースが不整合な状態にならない。

    Yields:
        AsyncSession: データベースセッション
    Raises:
        RuntimeError: データベースが初期化されていない場合
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    # async with: 非同期コンテキストマネージャ（自動的にセッションを閉じる）
    async with _session_factory() as session:
        try:
            yield session              # エンドポイントにセッションを渡す
            await session.commit()     # 処理成功 → 変更を確定
        except Exception:
            await session.rollback()   # 処理失敗 → 変更を取消
            raise                      # エラーを再送出（呼び出し元に伝える）


def get_engine() -> AsyncEngine:
    """
    データベースエンジンを取得する。

    マイグレーション（テーブル作成）等で直接エンジンが必要な場合に使用。

    Returns:
        AsyncEngine: データベースエンジン
    Raises:
        RuntimeError: データベースが初期化されていない場合
    """
    if _engine is None:
        raise RuntimeError("Database not initialized.")
    return _engine
