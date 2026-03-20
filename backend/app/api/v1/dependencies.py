# =============================================================================
# Step 12: 依存性注入（DI）— RAG対応版
# =============================================================================
#
# 【Step 8 からの変更点（Step 12）】
# Step 8: get_robot_repository + get_user_repository + get_current_user
# Step 12: + get_rag_repository + get_audit_service + Annotated エイリアス
#
# 【Annotated 型エイリアス（Step 12 新規）】
# Python 3.9+ の Annotated 型と FastAPI の Depends を組み合わせると、
# エンドポイントの引数定義がシンプルになる:
#
#   # Before（冗長）:
#   async def endpoint(repo: RAGRepository = Depends(get_rag_repository)):
#
#   # After（Annotated エイリアス）:
#   RagRepo = Annotated[RAGRepository, Depends(get_rag_repository)]
#   async def endpoint(repo: RagRepo):
#
# 💡 Annotated[T, metadata] は「T 型に追加情報（metadata）を付ける」構文。
# FastAPI はこの metadata に含まれる Depends() を自動的に解釈する。
#
# =============================================================================

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.infrastructure.database.connection import get_session
from app.infrastructure.database.repositories.robot_repo import (
    SQLAlchemyRobotRepository,
)
from app.infrastructure.database.repositories.user_repo import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.database.repositories.rag_repo import (
    SQLAlchemyRAGRepository,
)
from app.infrastructure.database.repositories.audit_repo import (
    SQLAlchemyAuditRepository,
)
from app.domain.repositories.robot_repo import RobotRepository
from app.domain.repositories.user_repo import UserRepository
from app.domain.repositories.rag_repository import RAGRepository
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.services.audit_service import AuditService
from app.domain.entities.user import User
from app.core.security import decode_token


# =============================================================================
# HTTPBearer — トークン抽出スキーム
# =============================================================================
#
# 【HTTPBearer とは？】
# FastAPI 組み込みのセキュリティスキーム。
# リクエストの Authorization ヘッダーから Bearer トークンを抽出する。
#
# 期待するヘッダー形式:
#   Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
#
# auto_error=False にすると、ヘッダーが無い場合に None を返す。
# （True だと自動で 403 を返す）
#
bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# リポジトリ DI（Step 7 と同じ + UserRepository 追加）
# =============================================================================

async def get_robot_repository(
    session: AsyncSession = Depends(get_session),
) -> RobotRepository:
    """ロボットリポジトリを注入する"""
    return SQLAlchemyRobotRepository(session)


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """ユーザーリポジトリを注入する"""
    return SQLAlchemyUserRepository(session)


# =============================================================================
# get_current_user — JWT からユーザーを取得（認証）
# =============================================================================
#
# 【認証の DI チェーン】
# 1. HTTPBearer が Authorization ヘッダーからトークンを抽出
# 2. decode_token() で JWT を検証・デコード
# 3. Payload の sub (user_id) で DB からユーザーを取得
# 4. ユーザーオブジェクトをエンドポイントに渡す
#
# エンドポイントでは `current_user: User = Depends(get_current_user)` と書くだけ！
#
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    JWT トークンからログイン中のユーザーを取得する

    【エラーケース】
    - トークンなし → 401 Unauthorized
    - トークン無効/期限切れ → 401 Unauthorized
    - ユーザーが存在しない → 401 Unauthorized
    - アカウント無効 → 403 Forbidden
    """
    # --- トークンの存在チェック ---
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です。ログインしてください。",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- JWT のデコードと検証 ---
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効または期限切れのトークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- トークンタイプの確認 ---
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アクセストークンを使用してください",
        )

    # --- ユーザーの取得 ---
    user_id = UUID(payload["sub"])
    user = await repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アカウントが無効化されています",
        )

    return user


# =============================================================================
# require_role — ロールベースアクセス制御（認可）
# =============================================================================
#
# 【高階関数パターン】
# require_role("admin") は「admin ロールを要求する DI 関数」を返す。
#
# 使い方:
#   @router.delete("/robots/{id}")
#   async def delete_robot(
#       user: User = Depends(require_role("admin", "operator")),
#   ):
#
# 【認証と認可の違い】
# 認証 (Authentication): 「あなたは誰？」 → get_current_user
# 認可 (Authorization):  「あなたは何ができる？」 → require_role
#
# 例:
#   viewer  → ロボット一覧の閲覧のみ
#   operator → ロボットの操作（CRUD）も可能
#   admin   → ユーザー管理も可能
#
def require_role(*allowed_roles: str):
    """
    特定のロールを要求する DI 関数を生成する

    【使い方】
    Depends(require_role("admin"))           → admin のみ
    Depends(require_role("admin", "operator")) → admin または operator
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"権限が不足しています。必要なロール: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


# =============================================================================
# RAG リポジトリ DI（Step 12 新規）
# =============================================================================
#
# 【RAGRepository の責務】
# - ドキュメント（RAGDocument）の CRUD
# - チャンク（DocumentChunk）の保存
# - ベクトル類似度検索（pgvector のコサイン距離を使用）
#

async def get_rag_repository(
    session: AsyncSession = Depends(get_session),
) -> RAGRepository:
    """RAG リポジトリを注入する"""
    return SQLAlchemyRAGRepository(session)


# =============================================================================
# 監査（Audit）サービス DI（Step 12 新規）
# =============================================================================
#
# 【AuditService の役割】
# ユーザーの操作を記録する（誰が、いつ、何をしたか）
# RAG では以下のアクションを記録:
#   - DOCUMENT_UPLOAD: ドキュメントのアップロード
#   - DOCUMENT_DELETE: ドキュメントの削除
#   - RAG_QUERY: 質問の実行
#

async def get_audit_service(
    session: AsyncSession = Depends(get_session),
) -> AuditService:
    """監査サービスを注入する"""
    repo = SQLAlchemyAuditRepository(session)
    return AuditService(audit_repo=repo)


# =============================================================================
# Annotated 型エイリアス（Step 12 新規）
# =============================================================================
#
# 💡 これらのエイリアスを使うと、エンドポイント定義が簡潔になる:
#
#   # エイリアスなし:
#   async def query(repo: RAGRepository = Depends(get_rag_repository)):
#
#   # エイリアスあり:
#   async def query(repo: RagRepo):
#
# 型チェッカー（mypy, pyright）も正しく解釈してくれる。
#

RagRepo = Annotated[RAGRepository, Depends(get_rag_repository)]
"""RAGRepository の Annotated エイリアス"""

AuditSvc = Annotated[AuditService, Depends(get_audit_service)]
"""AuditService の Annotated エイリアス"""

CurrentUser = Annotated[User, Depends(get_current_user)]
"""認証済みユーザーの Annotated エイリアス"""
