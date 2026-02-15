"""
Robot AI Web Application - FastAPI Main Application
"""

# =============================================================================
# FastAPI メインアプリケーション
# =============================================================================
#
# 【FastAPIとは？】
#   PythonでWeb APIを高速に構築するためのモダンなフレームワークです。
#   特徴:
#     - 自動的にAPIドキュメント（Swagger UI）を生成してくれる
#     - 型ヒント（Type Hints）を活用した入力バリデーション
#     - async/await による非同期処理のサポート（高い並行処理性能）
#     - Pythonの中で最も高速なWebフレームワークの1つ
#
# 【このファイルの役割】
#   アプリケーション全体の「エントリーポイント（入口）」です。
#   - アプリの起動/終了処理（lifespan）
#   - ミドルウェア（CORS等）の設定
#   - APIルーターの登録
#   - ヘルスチェックエンドポイントの定義
# =============================================================================

from __future__ import annotations

# 【asynccontextmanager とは？】
# 非同期版の「コンテキストマネージャ」を作るためのデコレータです。
# 通常の with 文は同期処理ですが、async with で非同期処理にも対応できます。
# ここでは FastAPI の lifespan（起動/終了の処理）を定義するために使います。
from contextlib import asynccontextmanager

from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

# 【CORSMiddleware とは？】
# CORS = Cross-Origin Resource Sharing（クロスオリジンリソース共有）
# ブラウザのセキュリティ機能で、異なるドメインからのAPIアクセスを制限します。
# 例: フロントエンド（localhost:3000）→ バックエンド（localhost:8000）への通信は
#     異なる「オリジン（origin）」なので、CORS設定がないとブラウザがブロックします。
# CORSMiddlewareを追加して許可設定をすることで、フロントエンドからのアクセスを可能にします。
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .config import get_settings
from .core.logging import setup_logging
from .infrastructure.database.connection import close_db, get_engine, init_db
from .infrastructure.redis.connection import close_redis, init_redis

# structlogのロガーを取得（このモジュール内でログ出力するため）
logger = structlog.get_logger()


# =============================================================================
# Lifespan（ライフスパン）: アプリケーションの起動と終了の処理
# =============================================================================
#
# 【lifespan とは？】
#   FastAPIアプリの「一生（ライフサイクル）」を管理する関数です。
#   - yield より前: アプリ起動時に実行される処理（DB接続、Redis接続など）
#   - yield: ここでアプリが稼働中（リクエストを受け付ける状態）
#   - yield より後: アプリ終了時に実行される処理（DB切断、リソース解放など）
#
# 【@asynccontextmanager の仕組み】
#   この関数を async with 文で使えるようにするデコレータです。
#   yield を境に「セットアップ」と「クリーンアップ」を分けます。
#   try-finally パターンの非同期版と考えるとわかりやすいです。
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown."""
    settings = get_settings()

    # ログの設定を初期化（構造化ログの設定 → core/logging.py を参照）
    setup_logging(settings.backend_log_level)

    logger.info("Starting Robot AI Backend", environment=settings.environment)

    # --- 起動処理 (Startup) ---

    # データベースの初期化（テーブル作成やコネクションプールの準備）
    # Initialize database
    await init_db(settings)
    logger.info("Database initialized")

    # Redisの初期化（キャッシュやメッセージキューとして使用）
    # Redis = インメモリデータストア。高速なデータの一時保存に使います。
    # Initialize Redis
    redis_client = await init_redis(settings.redis_url)
    logger.info("Redis connected")

    # --- 録画ワーカーの起動 ---
    # 【DI（依存性注入）パターンについて】
    # DI = Dependency Injection（依存性注入）
    # クラスが必要とする「依存オブジェクト」を外部から渡すデザインパターンです。
    #
    # 例: RecordingWorkerは RecordingService を必要としますが、
    #     自分で作らず、外部（ここ）から注入（渡）してもらいます。
    #
    # メリット:
    #   - テスト時にモック（偽物）を渡してテストしやすい
    #   - 各クラスの責任が明確になる（単一責任の原則）
    #   - 部品の入れ替えが容易（例: DBをPostgreSQLからMySQLに変更）
    #
    # 以下では手動でDIを行っています。本番環境ではDIコンテナ（injectorなど）を
    # 使うとより管理しやすくなります。

    # Start recording worker
    from .infrastructure.redis.recording_worker import RecordingWorker
    from .infrastructure.database.connection import get_session
    from .infrastructure.database.repositories.recording_repo import (
        SQLAlchemyRecordingRepository,
    )
    from .infrastructure.database.repositories.sensor_data_repo import (
        SQLAlchemySensorDataRepository,
    )
    from .domain.services.recording_service import RecordingService

    # Create a simple worker (simplified - in production you'd use proper DI)
    worker = None
    try:
        # セッション（DB接続のコンテキスト）を取得し、各リポジトリに渡す
        # リポジトリ = データベース操作を抽象化するクラス（CRUD操作を担当）
        # Get a session for the recording service
        session_gen = get_session()
        session = await session_gen.__anext__()
        recording_repo = SQLAlchemyRecordingRepository(session)
        sensor_repo = SQLAlchemySensorDataRepository(session)
        recording_svc = RecordingService(recording_repo, sensor_repo)

        worker = RecordingWorker(
            redis_client=redis_client,
            recording_service=recording_svc,
        )
        await worker.start()
        logger.info("Recording worker started")
    except Exception as e:
        logger.warning("Recording worker failed to start", error=str(e))

    # 【yield の役割】
    # ここで処理を「一時停止」し、アプリケーションが稼働状態に入ります。
    # FastAPIがHTTPリクエストを受け付けている間、ここで待機しています。
    # アプリ終了のシグナル（Ctrl+C や SIGTERM）を受け取ると、
    # yield の下の処理（シャットダウン処理）が実行されます。
    yield

    # --- 終了処理 (Shutdown) ---
    # アプリ終了時にリソースを解放します。
    # これをしないと、DB接続やRedis接続が残ったままになり、
    # リソースリーク（資源の無駄遣い）が発生します。
    # Shutdown
    logger.info("Shutting down...")
    if worker is not None:
        await worker.stop()
    await close_redis()
    await close_db()
    logger.info("Backend stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # 【FastAPIインスタンスの作成】
    # title, description, version はSwagger UI（自動生成されるAPIドキュメント）に表示されます。
    # docs_url="/docs" → ブラウザで http://localhost:8000/docs にアクセスするとAPI仕様が見れます。
    # redoc_url="/redoc" → 別のスタイルのAPIドキュメント（ReDoc形式）
    # lifespan → 上で定義した起動/終了の処理を紐づけます。
    app = FastAPI(
        title="Robot AI Web Application API",
        description="API for robot control, sensor data management, ML datasets, and RAG",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 【CORSミドルウェアの設定】
    # ミドルウェア = リクエストとレスポンスの「間」に入る処理のこと。
    # すべてのリクエスト/レスポンスに対して自動的に実行されます。
    #
    # allow_origins: どのオリジン（ドメイン）からのアクセスを許可するか
    # allow_credentials: Cookie等の認証情報を含むリクエストを許可するか
    # allow_methods: ["*"] = すべてのHTTPメソッド（GET, POST, PUT, DELETE等）を許可
    # allow_headers: ["*"] = すべてのHTTPヘッダーを許可
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 【APIルーターの登録】
    # api_router にはすべてのAPIエンドポイント（/api/v1/...）がまとめられています。
    # include_router() で、それらをアプリに一括登録します。
    # API routes
    app.include_router(api_router)

    # ==========================================================================
    # ヘルスチェック / レディネスチェック
    # ==========================================================================
    #
    # 【ヘルスチェック（Health Check）とは？】
    #   アプリケーションが「生きている（動いている）」かを確認するためのエンドポイントです。
    #   Docker や Kubernetes がコンテナの状態を監視するために定期的にアクセスします。
    #   正常なら {"status": "healthy"} を返します。
    #
    # 【レディネスチェック（Readiness Check）とは？】
    #   アプリが「リクエストを受け付ける準備ができている」かを確認します。
    #   ヘルスチェックとの違い:
    #     - ヘルスチェック: プロセスが生きているか（生存確認）
    #     - レディネスチェック: DBなど外部サービスとの接続が正常か（稼働確認）
    #   DBに接続できない場合、アプリは「生きている」が「準備できていない」状態です。
    # ==========================================================================

    # Health check
    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "healthy", "service": "backend"}

    @app.get("/ready")
    async def readiness_check() -> dict:
        # DBに実際にクエリを投げて接続を確認する
        try:
            engine = get_engine()
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return {"status": "ready"}
        except Exception:
            return {"status": "not_ready"}

    return app
