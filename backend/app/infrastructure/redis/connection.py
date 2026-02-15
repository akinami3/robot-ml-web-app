# ============================================================
# Redis 接続管理（Redis Connection Management）
# ============================================================
# Redis（インメモリデータストア）への非同期接続を管理するモジュール。
#
# 【Redis とは？】
# データをメモリ上に保存する超高速なデータベース。
# PostgreSQL（ディスクベース）よりも遥かに速いが、
# メモリ容量に制限があるため、一時的なデータに向いています。
#
# 【このプロジェクトでの Redis の用途】
# 1. Redis Streams: ゲートウェイとバックエンド間のメッセージキュー
#    → センサーデータやコマンドをリアルタイムに伝達
# 2. キャッシュ: 頻繁にアクセスされるデータの一時保存
# 3. Pub/Sub: リアルタイム通知の配信
#
# 【このモジュールのパターン】
# database/connection.py と同じ「モジュールレベル変数 + init/close/get 関数」
# パターンを使用。アプリ起動時に1回初期化し、全リクエストで共有する。
# ============================================================
"""Redis connection management."""

from __future__ import annotations

# redis.asyncio: Redis の非同期クライアントライブラリ
# 「as redis」でモジュール名を短縮してインポート
import redis.asyncio as redis

# モジュールレベルの変数（アプリ全体で1つの接続を共有）
_redis_client: redis.Redis | None = None


async def init_redis(url: str) -> redis.Redis:
    """
    Redis 接続を初期化する。

    アプリケーション起動時に main.py の lifespan 関数から呼ばれる。

    Args:
        url: Redis 接続URL（例: "redis://redis:6379/0"）
             redis:// → プロトコル
             redis → ホスト名（Docker コンテナ名）
             6379 → ポート番号（Redis のデフォルト）
             /0 → データベース番号（0〜15）
    Returns:
        Redis クライアントインスタンス
    """
    global _redis_client
    # from_url(): URL 文字列から Redis クライアントを作成
    # decode_responses=True: バイト列ではなく文字列で応答を返す
    _redis_client = redis.from_url(url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """
    Redis 接続を閉じる。

    アプリケーション終了時に呼ばれ、接続リソースを解放する。
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()  # 非同期で接続を閉じる
        _redis_client = None


def get_redis() -> redis.Redis:
    """
    Redis クライアントを取得する。

    FastAPI の Depends() で使用し、各リクエストハンドラに
    Redis クライアントを注入する。

    Returns:
        Redis クライアントインスタンス
    Raises:
        RuntimeError: Redis が初期化されていない場合
    """
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client
