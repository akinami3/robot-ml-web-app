# =============================================================================
# Step 8: FastAPI メインアプリケーション（認証対応版）
# =============================================================================
#
# 【Step 7 からの変更点】
# 1. 認証ルーター (auth.py) の登録
# 2. 初期 admin ユーザーの自動作成（lifespan 内）
# 3. バージョン更新
#
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy

from app.api.v1 import robots, auth
from app.infrastructure.database.connection import engine, async_session_factory
from app.infrastructure.database.repositories.user_repo import SQLAlchemyUserRepository
from app.domain.entities.user import User, UserRole
from app.core.security import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションの起動・終了処理"""
    # --- 起動時 ---
    print("🚀 データベース接続を確認中...")
    try:
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"⚠️  データベース接続失敗: {e}")

    # --- 初期 admin ユーザーの作成 ---
    #
    # 【なぜ自動作成？】
    # 最初のユーザーを登録するには、まず admin が必要。
    # しかし admin を作るための admin がいない → 「卵と鶏」問題。
    # 解決策: 起動時に初期 admin を自動作成する。
    #
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

    yield  # アプリケーション稼働中

    # --- 終了時 ---
    print("🛑 データベース接続を閉じています...")
    await engine.dispose()
    print("✅ クリーンアップ完了")


# =============================================================================
# FastAPI アプリケーション
# =============================================================================
app = FastAPI(
    title="Robot AI Web App API",
    version="0.3.0",
    description="Step 8: Authentication — JWT + bcrypt + RBAC",
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
# ルーターの登録
# =============================================================================
#
# 【Step 8 で追加した auth ルーター】
# prefix="/api/v1" で /api/v1/auth/login, /api/v1/auth/signup などが有効に。
#
app.include_router(
    robots.router,
    prefix="/api/v1",
    tags=["robots"],
)
app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["auth"],
)


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
        "version": "0.3.0",
    }
