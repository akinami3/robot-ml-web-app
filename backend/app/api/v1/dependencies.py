# =============================================================================
# Step 7: 依存性注入（Dependency Injection）モジュール
# =============================================================================
#
# 【依存性注入 (DI) とは？】
# クラスが必要な「依存物」を自分で作らず、外部から注入してもらうパターン。
#
# 例えば API エンドポイントがロボットリポジトリを使いたい場合:
#   ❌ 直接生成: repo = SQLAlchemyRobotRepository(session)  ← 密結合
#   ✅ DI:      repo = Depends(get_robot_repository)       ← 疎結合
#
# 【FastAPI の Depends() システム】
# FastAPI は Python のジェネレータ関数を使って DI を実現する。
#
#   async def get_session():        ← (1) DB セッションを生成
#       async with session_factory() as session:
#           yield session           ← (2) セッションを渡す
#                                   ← (3) リクエスト完了後に自動クリーンアップ
#
# yield の前: リソース確保（セッション生成）
# yield の値: エンドポイントに渡す値
# yield の後: リソース解放（セッション close）
#
# Go との比較:
#   Go:     ミドルウェアでリクエストコンテキストに DB を注入
#   Python: Depends() で関数パラメータに自動注入
#
# 【DI チェーン】
# Depends は連鎖できる:
#   get_session → get_robot_repository → エンドポイント関数
#   (DB接続)       (リポジトリ生成)       (ビジネスロジック)
#
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.robot_repo import (
    SQLAlchemyRobotRepository,
)
from app.domain.repositories.robot_repo import RobotRepository


# =============================================================================
# get_robot_repository — リポジトリの DI 関数
# =============================================================================
#
# 【型ヒントの意味】
# session: AsyncSession = Depends(get_session)
#   → get_session 関数を呼び出した結果（セッション）を session に注入
#
# -> RobotRepository
#   → 返り値は抽象型（インターフェース）
#   → 実際には SQLAlchemyRobotRepository だが、
#     API 層はインターフェースだけ知っていれば十分
#
async def get_robot_repository(
    session: AsyncSession = Depends(get_session),
) -> RobotRepository:
    """
    ロボットリポジトリを生成して注入する。

    【ポイント】
    1. API エンドポイントが必要とする「RobotRepository」を
       FastAPI の Depends が自動で生成・注入する。
    2. session は get_session() から自動で注入される（DI チェーン）。
    3. 返り値の型は「インターフェース」→ テスト時にモックに差し替え可能。
    """
    return SQLAlchemyRobotRepository(session)
