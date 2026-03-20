# =============================================================================
# Step 7: FastAPI メインアプリケーション（データベース対応版）
# =============================================================================
#
# 【Step 6 からの変更点】
# 1. lifespan コンテキストマネージャの追加（DB 接続の管理）
# 2. 説明文の更新（Step 7: Database）
#
# 【lifespan とは？】
# FastAPI 0.93+ で導入された、アプリケーションの
# 起動処理（startup）と終了処理（shutdown）を管理する仕組み。
#
# 旧方式:
#   @app.on_event("startup")
#   async def startup(): ...
#
# 新方式（lifespan）:
#   @asynccontextmanager
#   async def lifespan(app):
#       # 起動処理
#       yield
#       # 終了処理
#
# lifespan の方が:
# - 起動/終了が1つの関数にまとまる（見やすい）
# - リソースの確保/解放が try/finally で安全に書ける
# - テスト時にモックしやすい
#
# =============================================================================

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import robots
from app.infrastructure.database.connection import engine


# =============================================================================
# lifespan — アプリケーションのライフサイクル管理
# =============================================================================
#
# 【async context manager とは？】
# `async with` で使えるオブジェクト。
# Python の `contextlib.asynccontextmanager` デコレータで作成できる。
#
# yield の前: アプリ起動時に実行（DB 接続確認など）
# yield:      アプリが動いている間
# yield の後: アプリ終了時に実行（DB 接続のクリーンアップ）
#
# 【なぜ engine.dispose() が必要？】
# SQLAlchemy の AsyncEngine はコネクションプール（接続のプール）を持つ。
# アプリ終了時にプール内の全接続を適切に閉じないと、
# DB 側で接続がリークする。
#
@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションの起動・終了処理"""
    # --- 起動時 ---
    print("🚀 データベース接続を確認中...")
    # engine は connection.py で遅延作成されるため、
    # ここでテスト接続を行う（省略可能だがデバッグに便利）
    try:
        async with engine.begin() as conn:
            await conn.execute(
                # SQLAlchemy の text() を使わず、シンプルに接続テスト
                __import__("sqlalchemy").text("SELECT 1")
            )
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"⚠️ データベース接続失敗: {e}")
        print("  → PostgreSQL が起動しているか確認してください")

    yield  # ← アプリケーション稼働中

    # --- 終了時 ---
    print("🛑 データベース接続を閉じています...")
    await engine.dispose()
    print("✅ クリーンアップ完了")


# =============================================================================
# FastAPI アプリケーションの作成
# =============================================================================
app = FastAPI(
    title="Robot AI Web App API",
    version="0.2.0",
    description="Step 7: Database — PostgreSQL + SQLAlchemy による永続化",
    lifespan=lifespan,  # ← Step 7 で追加
)

# =============================================================================
# CORS ミドルウェア（Step 6 と同じ）
# =============================================================================
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
app.include_router(
    robots.router,
    prefix="/api/v1",
    tags=["robots"],
)


# =============================================================================
# ヘルスチェック（Step 7: DB 接続状態も確認）
# =============================================================================
#
# 【なぜ DB チェックを追加？】
# Step 6 ではバックエンド単体が動けば OK だった。
# Step 7 では DB が落ちていると API は正常に機能しない。
# ヘルスチェックで DB 接続も確認することで、
# Docker Compose のヘルスチェックが DB 障害を検知できる。
#
@app.get("/health")
async def health_check():
    """ヘルスチェック（DB 接続確認付き）"""
    db_ok = False
    try:
        async with engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
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
        "version": "0.2.0",
    }
