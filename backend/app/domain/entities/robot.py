# =============================================================================
# Step 7: Robot エンティティ — ドメイン層
# =============================================================================
#
# 【エンティティとは？】
# ビジネスロジックの中核となるデータ構造。
# DB のテーブル構造やフレームワークに依存しない「純粋な」データ表現。
#
# 【Clean Architecture の層構造】
#
#   ┌──────────────────────────────────────┐
#   │  API 層 (FastAPI Router)             │  ← 外部インターフェース
#   │  schemas.py (Pydantic)               │
#   ├──────────────────────────────────────┤
#   │  ドメイン層 (Entities, Repositories) │  ← ビジネスルール
#   │  robot.py ★ （このファイル）          │
#   │  robot_repo.py (インターフェース)     │
#   ├──────────────────────────────────────┤
#   │  インフラ層 (SQLAlchemy, DB 接続)     │  ← 技術的詳細
#   │  models.py, robot_repo.py (実装)      │
#   └──────────────────────────────────────┘
#
# 依存の方向: 外側 → 内側 (API → Domain ← Infrastructure)
# ドメイン層は何にも依存しない = テスト・差し替えが容易
#
# 【dataclass とは？】
# Python 3.7 で導入されたデコレータ。
# __init__, __repr__, __eq__ を自動生成してくれる。
#
# Pydantic の BaseModel に似ているが:
#   dataclass:  軽量、バリデーションなし、ドメインモデル向き
#   BaseModel:  バリデーション付き、API スキーマ向き
#
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


# =============================================================================
# ロボットの駆動タイプ
# =============================================================================
class RobotType(str, Enum):
    """ロボットの駆動方式"""
    DIFFERENTIAL = "differential"      # 差動二輪
    ACKERMANN = "ackermann"            # アッカーマン（自動車型）
    OMNIDIRECTIONAL = "omni"           # 全方向移動


class RobotStatus(str, Enum):
    """ロボットの状態"""
    OFFLINE = "offline"
    ONLINE = "online"
    ACTIVE = "active"
    ERROR = "error"
    MAINTENANCE = "maintenance"


# =============================================================================
# Robot エンティティ
# =============================================================================
#
# 【@dataclass の動作】
# デコレータを付けると、以下のメソッドが自動生成される:
#
#   __init__(self, id, name, ...):  フィールドを引数に取るコンストラクタ
#   __repr__(self):                 "Robot(id=..., name=...)" のような表示
#   __eq__(self, other):            全フィールドを比較する等値判定
#
# 【field(default_factory=...) とは？】
# ミュータブルなデフォルト値（list, dict, uuid4() など）には
# field(default_factory=...) を使う。
# 直接 `id: UUID = uuid4()` と書くと、全インスタンスが同じ UUID になる。
#
@dataclass
class Robot:
    """
    ロボットエンティティ

    ドメイン層のデータクラス。DB やフレームワークに依存しない。
    """
    name: str
    robot_type: RobotType = RobotType.DIFFERENTIAL
    description: str = ""
    status: RobotStatus = RobotStatus.OFFLINE

    # --- 自動生成フィールド ---
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
