# =============================================================================
# Step 12: スキーマ定義（RAG対応版）
# =============================================================================
#
# 【Step 8 からの変更点（Step 12）】
# ロボット・認証スキーマに加えて、RAG 関連のスキーマを追加する。
#
# 新しいスキーマ:
#   - RAGDocumentResponse: アップロード済みドキュメントの情報
#   - RAGQueryRequest: RAG クエリ（質問）リクエスト
#   - RAGQueryResponse: RAG 回答レスポンス
#
# 【Pydantic スキーマとは？（復習）】
# HTTP リクエスト/レスポンスの「形」を定義するクラス。
# FastAPI がリクエストのバリデーション（入力値チェック）と
# レスポンスのシリアライズ（Python → JSON 変換）を自動で行う。
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


# =============================================================================
# RAG スキーマ（Step 12 新規）
# =============================================================================
#
# 【RAG の 3 つの主要操作と対応するスキーマ】
#
# 1. ドキュメント登録:
#    - ファイルアップロード（multipart/form-data）
#    - レスポンス: RAGDocumentResponse（登録されたドキュメント情報）
#
# 2. ドキュメント一覧取得:
#    - レスポンス: list[RAGDocumentResponse]
#
# 3. 質問 → 回答:
#    - リクエスト: RAGQueryRequest（質問文 + 検索パラメータ）
#    - レスポンス: RAGQueryResponse（回答 + 参照ソース）
#
# 【top_k と min_similarity】
# top_k: ベクトル検索で取得する上位チャンク数
#   - 大きいほど多くの文脈を使う → 回答の網羅性が上がる
#   - 小さいほど最も関連性の高い情報だけ使う → 回答の精度が上がる
#
# min_similarity: 最小類似度の閾値（0.0 〜 1.0）
#   - 高い（0.8+）→ 非常に関連性の高い文書のみ使用
#   - 低い（0.3）→ 広い範囲から文脈を収集
#

class RAGDocumentResponse(BaseModel):
    """
    RAG ドキュメント情報レスポンス

    アップロードされたドキュメントの詳細情報を返す。
    chunk_count は、ドキュメントが何個のチャンク（断片）に分割されたかを示す。
    """
    id: UUID = Field(description="ドキュメントID")
    title: str = Field(description="ドキュメントタイトル")
    source: str = Field(description="ソース（ファイル名など）")
    file_type: str = Field(description="ファイル形式（pdf, txt, md）")
    file_size: int = Field(description="ファイルサイズ（バイト）")
    chunk_count: int = Field(description="分割されたチャンク数")
    created_at: datetime = Field(description="登録日時")


class RAGQueryRequest(BaseModel):
    """
    RAG クエリ（質問）リクエスト

    【使い方】
    {
      "question": "ロボットの安全停止機能について教えてください",
      "top_k": 5,
      "min_similarity": 0.3
    }

    top_k と min_similarity はオプション。省略するとデフォルト値が使われる。
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="質問文（1〜2000文字）",
        examples=["ロボットの緊急停止ボタンはどこにありますか？"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="検索する上位チャンク数（1〜20）",
    )
    min_similarity: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="最小類似度の閾値（0.0〜1.0）",
    )


class RAGQueryResponse(BaseModel):
    """
    RAG 回答レスポンス

    【sources フィールド】
    回答の根拠となったドキュメントチャンクのリスト。
    ユーザーが「この回答はどの文書に基づいているか」を確認できる。
    これは RAG の大きなメリット — 回答の出典が明確。
    """
    answer: str = Field(description="LLM の生成した回答")
    sources: list[dict] = Field(
        default=[],
        description="参照したドキュメントチャンク（タイトル、テキスト、類似度）",
    )
    context_used: int = Field(
        default=0,
        description="回答生成に使用したチャンク数",
    )
