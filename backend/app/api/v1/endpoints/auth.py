"""Authentication endpoints."""
# ============================================================
# 認証エンドポイント（auth.py）
# ============================================================
# このファイルは、ユーザー認証に関するAPIエンドポイントを定義します。
# 主な機能:
#   - ログイン（/login）: ユーザー名とパスワードでJWTトークンを取得
#   - ユーザー登録（/register）: 新しいアカウントを作成
#   - 自分の情報取得（/me）: ログイン中のユーザー情報を返す
#   - トークン更新（/refresh）: 期限切れ前にアクセストークンを再発行
# ============================================================

from __future__ import annotations

# --- 外部ライブラリのインポート ---
import structlog  # 構造化ログを出力するためのライブラリ
from fastapi import APIRouter, HTTPException, status
# APIRouter: エンドポイントをグループ化するルーター
# HTTPException: HTTPエラーレスポンスを返すための例外クラス
# status: HTTPステータスコード定数（401, 403, 409 など）

# --- 内部モジュールのインポート ---
from ....config import Settings, get_settings  # アプリ設定（JWT秘密鍵、有効期限など）
from ....core.security import create_tokens, hash_password, verify_password
# create_tokens: JWTアクセストークンとリフレッシュトークンを生成する関数
# hash_password: パスワードを安全にハッシュ化する関数
# verify_password: 入力パスワードとハッシュ値を比較する関数
from ....domain.entities.audit_log import AuditAction  # 監査ログのアクション種別
from ....domain.entities.user import User, UserRole  # ユーザーエンティティとロール定義
from ..dependencies import AuditSvc, CurrentUser, UserRepo
# AuditSvc: 監査ログサービス（DI = 依存性注入で自動的に渡される）
# CurrentUser: 認証済みの現在のユーザー（DI で自動取得）
# UserRepo: ユーザーデータベース操作用リポジトリ（DI で自動取得）
from ..schemas import (
    LoginRequest,        # ログインリクエストのスキーマ（username, password）
    RefreshTokenRequest, # トークン更新リクエストのスキーマ（refresh_token）
    TokenResponse,       # トークンレスポンスのスキーマ（access_token, refresh_token, expires_in）
    UserCreate,          # ユーザー作成リクエストのスキーマ（username, email, password, role）
    UserResponse,        # ユーザー情報レスポンスのスキーマ
)

# ロガーの初期化（デバッグやエラー追跡に使用）
logger = structlog.get_logger()

# "/auth" プレフィックス付きのルーターを作成
# 例: /api/v1/auth/login, /api/v1/auth/register のようなURLになる
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# ログインエンドポイント（POST /auth/login）
# ============================================================
# 処理の流れ:
#   1. ユーザー名でデータベースからユーザーを検索
#   2. パスワードを検証（ハッシュ値と比較）
#   3. アカウントが有効か確認
#   4. JWTトークン（アクセス＋リフレッシュ）を生成
#   5. 監査ログにログイン記録を保存
#   6. トークンをレスポンスとして返す
# ============================================================
@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,    # リクエストボディ（username と password を含む）
    user_repo: UserRepo,   # ユーザーリポジトリ（FastAPIのDIで自動注入される）
    audit_svc: AuditSvc,   # 監査ログサービス（FastAPIのDIで自動注入される）
):
    # async def = 非同期関数（await を使ってデータベース操作などを
    # ブロックせずに待てる。複数リクエストを同時処理するために重要）

    # ステップ1: ユーザー名でユーザーを検索
    user = await user_repo.get_by_username(body.username)

    # ステップ2: ユーザーが存在しない、またはパスワードが一致しない場合
    if user is None or not verify_password(body.password, user.hashed_password):
        # HTTP 401 Unauthorized: 認証に失敗した（ユーザー名またはパスワードが間違い）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # ステップ3: アカウントが無効化されている場合
    if not user.is_active:
        # HTTP 403 Forbidden: 認証はできたが、アクセスが禁止されている
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # ステップ4: JWTトークンを生成
    settings = get_settings()  # アプリ設定を取得（秘密鍵、有効期限など）
    tokens = create_tokens(
        user_id=str(user.id),                              # ユーザーID（文字列に変換）
        role=user.role.value,                              # ユーザーの権限ロール
        private_key=settings.jwt_private_key,              # JWT署名用の秘密鍵
        access_expire_minutes=settings.jwt_access_expire_minutes,  # アクセストークンの有効期限（分）
        refresh_expire_days=settings.jwt_refresh_expire_days,      # リフレッシュトークンの有効期限（日）
    )

    # ステップ5: 監査ログにログインアクションを記録
    await audit_svc.log_action(
        user_id=user.id,
        action=AuditAction.LOGIN,
    )

    # ステップ6: トークン情報をレスポンスとして返す
    return TokenResponse(
        access_token=tokens["access_token"],    # APIアクセス用のトークン
        refresh_token=tokens["refresh_token"],  # トークン更新用のトークン
        expires_in=settings.jwt_access_expire_minutes * 60,  # 有効期限（秒単位に変換）
    )


# ============================================================
# ユーザー登録エンドポイント（POST /auth/register）
# ============================================================
# 処理の流れ:
#   1. ユーザー名の重複チェック
#   2. メールアドレスの重複チェック
#   3. ロール（権限）の設定
#   4. パスワードをハッシュ化してユーザーを作成
#   5. 作成したユーザー情報を返す
# ============================================================
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserCreate,      # リクエストボディ（username, email, password, role を含む）
    user_repo: UserRepo,   # ユーザーリポジトリ（DIで自動注入）
):
    # ステップ1: ユーザー名の重複チェック
    existing = await user_repo.get_by_username(body.username)
    if existing is not None:
        # HTTP 409 Conflict: リソースが既に存在する（ユーザー名が使用済み）
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    # ステップ2: メールアドレスの重複チェック
    existing_email = await user_repo.get_by_email(body.email)
    if existing_email is not None:
        # HTTP 409 Conflict: メールアドレスが既に登録されている
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # ステップ3: ロール（権限）を設定
    # 無効なロールが指定された場合は VIEWER（閲覧のみ）をデフォルトにする
    try:
        role = UserRole(body.role)
    except ValueError:
        role = UserRole.VIEWER

    # ステップ4: ユーザーエンティティを作成
    # hash_password() でパスワードを安全にハッシュ化（平文では保存しない）
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=role,
    )

    # ステップ5: データベースにユーザーを保存し、レスポンスを返す
    created = await user_repo.create(user)
    return UserResponse(
        id=created.id,
        username=created.username,
        email=created.email,
        role=created.role.value,
        is_active=created.is_active,
        created_at=created.created_at,
    )


# ============================================================
# 自分の情報取得エンドポイント（GET /auth/me）
# ============================================================
# 認証済みのユーザー情報を返す。
# CurrentUser はDIで自動的にJWTトークンからユーザーを特定する。
# ============================================================
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    # current_user: 認証ミドルウェアが自動的に解決する現在のユーザー
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


# ============================================================
# トークン更新エンドポイント（POST /auth/refresh）
# ============================================================
# 処理の流れ:
#   1. リフレッシュトークンをデコード（復号）して検証
#   2. トークンの種類が "refresh" であることを確認
#   3. ユーザーが存在し、アカウントが有効か確認
#   4. 新しいアクセストークンとリフレッシュトークンを発行
#
# なぜ必要？:
#   アクセストークンは短い有効期限（例: 30分）を持つ。
#   期限が切れる前にリフレッシュトークンで新しいトークンを取得できる。
#   これにより、ユーザーは再ログインせずにセッションを継続できる。
# ============================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,  # リクエストボディ（refresh_token を含む）
    user_repo: UserRepo,        # ユーザーリポジトリ（DIで自動注入）
):
    from ....core.security import decode_token  # トークンをデコードする関数

    # ステップ1: リフレッシュトークンをデコードして検証
    settings = get_settings()
    payload = decode_token(body.refresh_token, settings.jwt_public_key)

    # ステップ2: トークンが無効、またはリフレッシュトークンでない場合
    if payload is None or payload.get("type") != "refresh":
        # HTTP 401 Unauthorized: トークンが無効
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    from uuid import UUID  # UUID型（ユーザーIDの形式）

    # ステップ3: トークンに含まれるユーザーIDでユーザーを検索
    user = await user_repo.get_by_id(UUID(payload["sub"]))
    if user is None or not user.is_active:
        # HTTP 401 Unauthorized: ユーザーが存在しないか無効
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # ステップ4: 新しいトークンペアを生成
    tokens = create_tokens(
        user_id=str(user.id),
        role=user.role.value,
        private_key=settings.jwt_private_key,
        access_expire_minutes=settings.jwt_access_expire_minutes,
        refresh_expire_days=settings.jwt_refresh_expire_days,
    )

    # 新しいトークンをレスポンスとして返す
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=settings.jwt_access_expire_minutes * 60,
    )
