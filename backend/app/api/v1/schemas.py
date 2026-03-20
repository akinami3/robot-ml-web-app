# =============================================================================
# Step 8: 認証スキーマ — リクエスト/レスポンスの型定義
# =============================================================================
#
# 【Step 7 からの変更点】
# ロボット関連のスキーマに加えて、認証関連のスキーマを追加する。
#
# 新しいスキーマ:
#   - UserCreate: ユーザー登録リクエスト
#   - LoginRequest: ログインリクエスト
#   - TokenResponse: JWT トークンのレスポンス
#   - UserResponse: ユーザー情報レスポンス（パスワードは含まない！）
#
# =============================================================================

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# Enum（Step 7 と同一 + UserRole 追加）
# =============================================================================

class RobotType(str, Enum):
    """ロボットの駆動タイプ"""
    DIFFERENTIAL = "differential"
    ACKERMANN = "ackermann"
    OMNIDIRECTIONAL = "omni"


class RobotStatus(str, Enum):
    """ロボットの状態"""
    OFFLINE = "offline"
    ONLINE = "online"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class UserRole(str, Enum):
    """ユーザーの役割"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


# =============================================================================
# Robot スキーマ（Step 7 と同一）
# =============================================================================

class RobotCreate(BaseModel):
    """ロボット登録リクエスト"""
    name: str = Field(
        ..., min_length=1, max_length=100,
        description="ロボットの名前", examples=["TurtleBot3"],
    )
    robot_type: RobotType = Field(
        default=RobotType.DIFFERENTIAL, description="駆動タイプ",
    )
    description: str = Field(
        default="", max_length=500, description="説明文（任意）",
    )


class RobotUpdate(BaseModel):
    """ロボット更新リクエスト（部分更新）"""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    robot_type: RobotType | None = None
    description: str | None = Field(default=None, max_length=500)
    status: RobotStatus | None = None


class RobotResponse(BaseModel):
    """ロボット情報レスポンス"""
    id: UUID = Field(description="一意な識別子")
    name: str = Field(description="ロボット名")
    robot_type: RobotType = Field(description="駆動タイプ")
    description: str = Field(description="説明文")
    status: RobotStatus = Field(description="現在の状態")
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")


class RobotListResponse(BaseModel):
    """ロボット一覧レスポンス"""
    robots: list[RobotResponse]
    total: int = Field(description="総件数")


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス"""
    message: str


# =============================================================================
# 認証スキーマ（Step 8 新規）
# =============================================================================

class UserCreate(BaseModel):
    """
    ユーザー登録（サインアップ）リクエスト

    【バリデーションルール】
    username: 3-50文字、必須
    email: 有効なメールアドレス形式
    password: 8文字以上（平文で送信 → サーバーで bcrypt ハッシュ化）

    【注意】
    パスワードはここでは平文（str）で受け取る。
    Pydantic スキーマはリクエストのバリデーション用であり、
    DB に保存する前に必ず bcrypt でハッシュ化する。
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="ユーザー名（3-50文字）",
        examples=["taro"],
    )
    email: str = Field(
        ...,
        description="メールアドレス",
        examples=["taro@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="パスワード（8文字以上）",
        examples=["password123"],
    )


class LoginRequest(BaseModel):
    """
    ログインリクエスト

    【なぜ Username + Password？】
    最もシンプルな認証方式。
    OAuth2, SAML, OIDC などは Step 13 で扱う。
    """
    username: str = Field(..., description="ユーザー名")
    password: str = Field(..., description="パスワード")


class TokenResponse(BaseModel):
    """
    JWT トークンレスポンス

    【各フィールドの説明】
    access_token:  API アクセスに使うトークン（短い有効期限）
    refresh_token: Access Token を再発行するトークン（長い有効期限）
    token_type:    "bearer" — Authorization ヘッダーの形式を指定
                   → Authorization: Bearer <access_token>

    【Bearer Token とは？】
    "Bearer" は「持参人」の意味。
    このトークンを「持っている人」がアクセス権を持つ。
    RFC 6750 で標準化されている。
    """
    access_token: str = Field(description="アクセストークン")
    refresh_token: str = Field(description="リフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")


class TokenRefreshRequest(BaseModel):
    """トークンリフレッシュリクエスト"""
    refresh_token: str = Field(..., description="リフレッシュトークン")


class UserResponse(BaseModel):
    """
    ユーザー情報レスポンス

    【重要: パスワードは含めない！】
    hashed_password をレスポンスに含めると、
    攻撃者がオフラインでブルートフォースできてしまう。
    レスポンススキーマにパスワード関連フィールドは絶対に入れない。
    """
    id: UUID = Field(description="ユーザーID")
    username: str = Field(description="ユーザー名")
    email: str = Field(description="メールアドレス")
    role: UserRole = Field(description="ロール")
    is_active: bool = Field(description="アカウント有効")
    created_at: datetime = Field(description="作成日時")
