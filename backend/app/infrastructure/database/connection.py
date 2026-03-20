# =============================================================================
# Step 7: データベース接続管理
# =============================================================================
#
# 【SQLAlchemy 2.0 の非同期モード】
# SQLAlchemy は Python の最も人気のある ORM (Object-Relational Mapper)。
# バージョン 2.0 から、async/await を使った非同期 DB アクセスが正式サポート。
#
# 【ORM とは？】
# Object-Relational Mapping の略。
# Python のクラス（オブジェクト）と DB のテーブル（リレーション）を対応付ける。
#
#   Python:  robot = Robot(name="TurtleBot3", status="online")
#   SQL:     INSERT INTO robots (name, status) VALUES ('TurtleBot3', 'online');
#
# ORM を使うと SQL を直接書かずに DB 操作ができる。
# ただし複雑なクエリでは SQL の知識も必要。
#
# 【接続プールとは？】
# DB への接続はコストが高い（TCP ハンドシェイク、認証など）。
# そこで接続を使い回す「プール」を用意する。
# SQLAlchemy のエンジンが接続プールを管理する。
#
# pool_size=5:   プールに保持する接続数
# max_overflow=10: pool_size を超えて追加で作れる接続数
# → 最大 15 同時接続
#
# =============================================================================

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# =============================================================================
# エンジン（Engine）の作成
# =============================================================================
#
# 【Engine とは？】
# DB への接続を管理する中心的なオブジェクト。
# 接続プールを内部に持ち、セッションに接続を貸し出す。
#
# echo=True にすると、実行される SQL 文がログに出力される。
# → 開発中はデバッグに便利だが、本番では False にする。
#
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,       # True なら SQL ログを出力
    pool_size=5,               # 常時保持する接続数
    max_overflow=10,           # 超過分の許容数
    pool_pre_ping=True,        # 接続がまだ有効かチェック（切断検知）
)

# =============================================================================
# セッションファクトリ
# =============================================================================
#
# 【Session とは？】
# DB トランザクション（一連の操作）を管理するオブジェクト。
# 1リクエストに対して1セッション（Unit of Work パターン）。
#
# 【async_sessionmaker とは？】
# AsyncSession を生成するファクトリ。
# 毎回 AsyncSession(...) と書く代わりに、設定を事前に共有できる。
#
# expire_on_commit=False:
#   コミット後もオブジェクトの属性にアクセスできるようにする。
#   True（デフォルト）だと、コミット後にアクセスすると
#   遅延読み込みが発生してエラーになることがある。
#
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# get_session — リクエストごとのセッション取得
# =============================================================================
#
# 【async generator とは？】
# `yield` を使った非同期ジェネレーター。
# FastAPI の Depends() で使うと、以下のライフサイクルが保証される:
#
#   1. yield の前: セッションを作成して渡す
#   2. yield: エンドポイント関数がセッションを使用
#   3. yield の後: セッションを自動で閉じる
#
# これにより、セッションの閉じ忘れを防げる。
# try/finally パターンで確実にクリーンアップする。
#
# 【Go との比較】
# Go: defer conn.Close()
# Python: async with / async generator + finally
#
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
