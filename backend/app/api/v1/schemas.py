# =============================================================================
# Step 6: Pydantic スキーマ — リクエスト/レスポンスの型定義
# =============================================================================
#
# 【Pydantic とは？】
# Python のデータバリデーションライブラリ。
# クラスにフィールドの型を宣言するだけで、自動でバリデーションが行われる。
#
# Go との比較:
#   Go:      type Robot struct { Name string `json:"name" validate:"required"` }
#   Pydantic: class Robot(BaseModel): name: str
#
# FastAPI は Pydantic を内部的に使用しており、
# リクエストボディの JSON を自動で Pydantic モデルに変換し、
# 型が合わなければ 422 Unprocessable Entity エラーを返す。
#
# 【BaseModel の主な機能】
# 1. 型バリデーション: str に int を渡すとエラー
# 2. デフォルト値: `field: str = "default"` で省略可能に
# 3. JSON シリアライズ: `.model_dump()` で辞書に変換
# 4. 自動ドキュメント: FastAPI の /docs に型情報が表示される
#
# =============================================================================

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# Enum（列挙型）
# =============================================================================
#
# 【Enum とは？】
# 取りうる値を限定する型。
# 例: RobotType は "differential" か "ackermann" のみ許可。
# 文字列そのものだと typo（例: "diferential"）が検出できないが、
# Enum なら不正値を Pydantic が自動で拒否する。
#
# Go との比較:
#   Go:     type RobotType string; const ( Differential RobotType = "differential" )
#   Python: class RobotType(str, Enum): DIFFERENTIAL = "differential"
#
class RobotType(str, Enum):
    """ロボットの駆動タイプ"""
    DIFFERENTIAL = "differential"   # 差動二輪（左右の車輪で旋回）
    ACKERMANN = "ackermann"         # アッカーマン（自動車型ステアリング）
    OMNIDIRECTIONAL = "omni"        # 全方向移動（メカナムホイールなど）


class RobotStatus(str, Enum):
    """ロボットの状態"""
    OFFLINE = "offline"         # 未接続
    ONLINE = "online"           # 接続中・待機
    ACTIVE = "active"           # 稼働中
    ERROR = "error"             # エラー状態
    MAINTENANCE = "maintenance" # メンテナンス中


# =============================================================================
# リクエストスキーマ
# =============================================================================
#
# 【Create と Update を分ける理由】
# Create: すべての必須フィールドが必要
# Update: 一部のフィールドだけ更新できる（PATCH に相当）
#
# 例: ロボット名だけ変更したい場合、
# Update スキーマを使えば name だけ送ればよい。
#

class RobotCreate(BaseModel):
    """ロボット登録リクエスト"""
    name: str = Field(
        ...,                         # ... = 必須フィールド
        min_length=1,                # 空文字を禁止
        max_length=100,              # 長すぎる名前を禁止
        description="ロボットの名前",
        examples=["TurtleBot3"],
    )
    robot_type: RobotType = Field(
        default=RobotType.DIFFERENTIAL,
        description="駆動タイプ",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="説明文（任意）",
    )


class RobotUpdate(BaseModel):
    """
    ロボット更新リクエスト（部分更新 = PATCH）

    【Optional フィールド】
    `name: str | None = None` は「name は str か None、デフォルトは None」の意味。
    None のフィールドは「変更しない」と解釈し、更新クエリから除外する。
    """
    name: str | None = Field(default=None, min_length=1, max_length=100)
    robot_type: RobotType | None = None
    description: str | None = Field(default=None, max_length=500)
    status: RobotStatus | None = None


# =============================================================================
# レスポンススキーマ
# =============================================================================
#
# 【リクエストとレスポンスでスキーマを分ける理由】
# リクエスト: クライアントが送るデータ（id は自動生成のため含めない）
# レスポンス: サーバーが返すデータ（id, created_at などを含める）
#
# この分離により:
# 1. クライアントが id を偽造するのを防げる
# 2. サーバー内部のフィールド（パスワードハッシュなど）を漏らさない
# 3. API ドキュメントが明確になる
#

class RobotResponse(BaseModel):
    """
    ロボット情報レスポンス

    【model_config の ConfigDict】
    from_attributes=True にすると、ORM オブジェクト（SQLAlchemy モデル）から
    自動で RobotResponse を生成できる。Step 7 で ORM を導入したときに使う。
    Step 6 では in-memory の辞書から生成するので、必須ではない。
    """
    id: UUID = Field(description="一意な識別子（UUID v4）")
    name: str = Field(description="ロボット名")
    robot_type: RobotType = Field(description="駆動タイプ")
    description: str = Field(description="説明文")
    status: RobotStatus = Field(description="現在の状態")
    created_at: datetime = Field(description="作成日時")
    updated_at: datetime = Field(description="更新日時")


class RobotListResponse(BaseModel):
    """
    ロボット一覧レスポンス

    【なぜリストを直接返さない？】
    `[RobotResponse, ...]` でも動くが、
    メタ情報（total 件数、ページネーション情報など）を付けるために
    ラッパーオブジェクトにする。これは REST API のベストプラクティス。
    """
    robots: list[RobotResponse]
    total: int = Field(description="総件数")


class MessageResponse(BaseModel):
    """汎用メッセージレスポンス"""
    message: str
