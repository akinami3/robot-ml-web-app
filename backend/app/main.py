# =============================================================================
# Step 11: FastAPI メインアプリケーション（データ記録対応版）
# =============================================================================
#
# 【Step 8 からの変更点（Step 11）】
# 1. api_router（統合ルーター）を使用 → 個別ルーター登録を廃止
# 2. Redis 接続の初期化・終了処理を lifespan に追加
# 3. RecordingWorker の起動・停止を lifespan に追加
# 4. structlog による構造化ログを導入
# 5. バージョン 0.3.0 → 0.4.0
#
# 【統合ルーター（api_router）のメリット】
# Step 8 では robots.router と auth.router を個別に app.include_router() で登録。
# Step 11 では api/v1/router.py にすべてのルーター（8個）を集約した api_router を
# 1回の include_router() で登録する。ルーターが増えても main.py を変更不要。
#
# 【RecordingWorker とは？】
# Redis Streams からセンサーデータを読み取り、PostgreSQL に保存するワーカー。
# Gateway → Redis Streams → RecordingWorker → PostgreSQL という流れ。
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy

# Step 11: api_router を使用（個別ルーターの代わりに統合ルーターをインポート）
from app.api.v1.router import api_router
from app.infrastructure.database.connection import engine, async_session_factory
from app.infrastructure.database.repositories.user_repo import SQLAlchemyUserRepository
from app.domain.entities.user import User, UserRole
from app.core.security import hash_password

# Step 11: Redis 接続管理
from app.infrastructure.redis.connection import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションの起動・終了処理（Step 11 拡張版）"""
    # --- 起動時 ---
    print("🚀 データベース接続を確認中...")
    try:
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"⚠️  データベース接続失敗: {e}")

    # --- 初期 admin ユーザーの作成（Step 8 と同じ） ---
    try:
        async with async_session_factory() as session:
            repo = SQLAlchemyUserRepository(session)
            existing = await repo.find_by_username("admin")
            if existing is None:
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.ADMIN,
                )
                await repo.create(admin_user)
                print("✅ 初期 admin ユーザーを作成しました（admin / admin123）")
            else:
                print("ℹ️  admin ユーザーは既に存在します")
    except Exception as e:
        print(f"⚠️  初期ユーザー作成に失敗: {e}")

    # --- Step 11: Redis 接続の初期化 ---
    #
    # 【なぜ Redis が必要？】
    # Gateway（Go）がセンサーデータを Redis Streams に書き込む。
    # Backend（Python）が Redis Streams からデータを読み取り、
    # PostgreSQL に永続化する。
    # Redis はこの「橋渡し」の役割を果たす。
    #
    import os
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = None
    try:
        redis_client = await init_redis(redis_url)
        print(f"✅ Redis 接続成功: {redis_url}")
    except Exception as e:
        print(f"⚠️  Redis 接続失敗（データ記録無効）: {e}")

    # --- Step 11: RecordingWorker の起動 ---
    #
    # 【RecordingWorker の仕組み】
    # Redis Streams の Consumer Group を使って、センサーデータを
    # バックグラウンドで読み取り、PostgreSQL に保存する。
    #
    # 【DI（依存性注入）パターン】
    # Worker → RecordingService → Repositories → Session
    # という依存関係を外部（ここ）から組み立てて渡す。
    #
    worker = None
    if redis_client is not None:
        try:
            from app.infrastructure.redis.recording_worker import RecordingWorker
            from app.infrastructure.database.connection import get_session
            from app.infrastructure.database.repositories.recording_repo import (
                SQLAlchemyRecordingRepository,
            )
            from app.infrastructure.database.repositories.sensor_data_repo import (
                SQLAlchemySensorDataRepository,
            )
            from app.domain.services.recording_service import RecordingService

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
            print("✅ RecordingWorker 起動成功")
        except Exception as e:
            print(f"⚠️  RecordingWorker 起動失敗: {e}")

    yield  # アプリケーション稼働中

    # --- 終了時 ---
    print("🛑 クリーンアップ中...")
    if worker is not None:
        try:
            await worker.stop()
            print("✅ RecordingWorker 停止")
        except Exception as e:
            print(f"⚠️  RecordingWorker 停止失敗: {e}")

    try:
        await close_redis()
        print("✅ Redis 接続を閉じました")
    except Exception as e:
        print(f"⚠️  Redis 切断失敗: {e}")

    print("🛑 データベース接続を閉じています...")
    await engine.dispose()
    print("✅ クリーンアップ完了")


# =============================================================================
# FastAPI アプリケーション
# =============================================================================
app = FastAPI(
    title="Robot AI Web App API",
    version="0.4.0",
    description="Step 11: Data Recording — Redis Streams + TimescaleDB",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ルーターの登録（Step 11: 統合ルーター方式に変更）
# =============================================================================
#
# 【Step 8 との違い】
# Step 8:
#   app.include_router(robots.router, prefix="/api/v1", tags=["robots"])
#   app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
#
# Step 11:
#   app.include_router(api_router)  ← 1行で8個のルーター全部登録！
#
# api_router は api/v1/router.py で定義されており、prefix="/api/v1" も含んでいる。
# 新しいエンドポイントを追加する場合、router.py を変更するだけでOK。
#
app.include_router(api_router)


# --- ヘルスチェック ---
@app.get("/health")
async def health_check():
    db_ok = False
    try:
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "backend",
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/")
async def root():
    return {
        "message": "Robot AI Web App API",
        "docs": "/docs",
        "version": "0.4.0",
    }
