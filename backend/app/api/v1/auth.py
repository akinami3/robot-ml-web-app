# =============================================================================
# Step 8: 認証エンドポイント — サインアップ・ログイン・リフレッシュ
# =============================================================================
#
# 【認証フローの全体像】
#
# 1. サインアップ (POST /auth/signup):
#    ユーザー名 + パスワード → bcrypt ハッシュ → DB に保存
#
# 2. ログイン (POST /auth/login):
#    ユーザー名 + パスワード → bcrypt 照合 → JWT 生成 → 返却
#
# 3. API リクエスト (GET /robots など):
#    Authorization: Bearer <access_token> ヘッダー付きでリクエスト
#    → JWT を検証 → ユーザー情報を取得 → エンドポイント処理
#
# 4. トークンリフレッシュ (POST /auth/refresh):
#    Refresh Token → 検証 → 新しい Access Token を発行
#
# 【セキュリティのポイント】
# - パスワードは平文でログに出力しない
# - ログインエラーで「ユーザーが存在しない」か「パスワードが間違い」かを
#   区別しない → 攻撃者へのヒントを減らす
#
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import (
    LoginRequest,
    MessageResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.api.v1.dependencies import get_user_repository, get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repo import UserRepository

router = APIRouter()


# =============================================================================
# POST /auth/signup — ユーザー登録
# =============================================================================
#
# 【処理フロー】
# 1. ユーザー名の重複チェック
# 2. メールアドレスの重複チェック
# 3. パスワードを bcrypt でハッシュ化
# 4. ユーザーエンティティを作成して DB に保存
# 5. ユーザー情報を返す（パスワードは含めない）
#
@router.post(
    "/auth/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
)
async def signup(
    body: UserCreate,
    repo: UserRepository = Depends(get_user_repository),
):
    """新しいユーザーを登録する"""

    # --- ユーザー名の重複チェック ---
    existing = await repo.find_by_username(body.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このユーザー名は既に使用されています",
        )

    # --- メールアドレスの重複チェック ---
    existing_email = await repo.find_by_email(body.email)
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に使用されています",
        )

    # --- パスワードのハッシュ化 ---
    # 平文パスワードを bcrypt でハッシュ化して保存。
    # body.password は以降使わない（メモリから消える）。
    hashed = hash_password(body.password)

    # --- ユーザーエンティティの作成 ---
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hashed,
        role=UserRole.VIEWER,  # デフォルトは閲覧者
    )

    created = await repo.create(user)

    return UserResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        role=created.role.value,
        is_active=created.is_active,
        created_at=created.created_at,
    )


# =============================================================================
# POST /auth/login — ログイン（トークン発行）
# =============================================================================
#
# 【認証の流れ】
# 1. username で DB からユーザーを検索
# 2. パスワードを bcrypt で照合
# 3. 一致すれば Access Token + Refresh Token を発行
#
# 【なぜエラーメッセージを統一する？】
# 「ユーザーが見つかりません」と「パスワードが違います」を分けると、
# 攻撃者がユーザーの存在を確認できてしまう。
# 統一メッセージ「ユーザー名またはパスワードが正しくありません」にする。
#
@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="ログイン",
)
async def login(
    body: LoginRequest,
    repo: UserRepository = Depends(get_user_repository),
):
    """ユーザー名とパスワードでログインし、JWT トークンを取得する"""

    # --- ユーザーの検索 ---
    user = await repo.find_by_username(body.username)

    # --- 認証チェック ---
    # ユーザーが存在しない OR パスワードが一致しない → 同じエラー
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- アカウント無効チェック ---
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アカウントが無効化されています",
        )

    # --- JWT トークンの生成 ---
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# =============================================================================
# POST /auth/refresh — トークンリフレッシュ
# =============================================================================
#
# 【なぜリフレッシュが必要？】
# Access Token の有効期限が切れたとき、
# ユーザーに再ログインさせるのは UX が悪い。
# Refresh Token があれば、バックグラウンドで自動更新できる。
#
@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="トークンリフレッシュ",
)
async def refresh_token(
    body: TokenRefreshRequest,
    repo: UserRepository = Depends(get_user_repository),
):
    """Refresh Token を使って新しい Access Token を取得する"""

    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです",
        )

    # --- トークンタイプの確認 ---
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンではありません",
        )

    # --- ユーザーの存在確認 ---
    from uuid import UUID
    user_id = UUID(payload["sub"])
    user = await repo.get_by_id(user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つからないか無効化されています",
        )

    # --- 新しいトークンを発行 ---
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value,
    )
    new_refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# =============================================================================
# GET /auth/me — 現在のユーザー情報を取得
# =============================================================================
#
# 【認証済みエンドポイントの例】
# get_current_user が Depends() で注入される。
# JWT から自動でユーザー情報を取得してくれる。
#
@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="ログイン中のユーザー情報",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """現在ログイン中のユーザー情報を返す"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
