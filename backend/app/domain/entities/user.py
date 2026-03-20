# =============================================================================
# Step 8: ユーザーエンティティ — 認証・認可のドメインモデル
# =============================================================================
#
# 【このファイルの位置づけ】
# ドメイン層のエンティティ。DB や Web フレームワークに依存しない。
# ユーザーの「ビジネスルール」を表現する。
#
# 【なぜ Robot と同じくドメイン層に？】
# Clean Architecture では、ビジネスの中心概念をドメイン層に置く。
# 「ユーザー」は認証・認可というビジネスルールの主役。
#
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


# =============================================================================
# UserRole — ロールベースアクセス制御 (RBAC)
# =============================================================================
#
# 【RBAC とは？】
# Role-Based Access Control の略。
# ユーザーに「ロール（役割）」を割り当て、
# ロールごとにアクセス権限を制御するモデル。
#
# 例:
#   admin:    全操作が可能（ユーザー管理、ロボット削除など）
#   operator: ロボットの操作が可能（制御、状態変更）
#   viewer:   閲覧のみ（一覧表示、詳細閲覧）
#
# 【なぜ RBAC？】
# ユーザーごとに個別に権限を設定する方式（ACL）は、
# ユーザーが増えると管理が大変。
# ロールにまとめることで権限管理がシンプルになる。
#
# AWS IAM、GitHub、Kubernetes なども RBAC を採用している。
#
class UserRole(str, Enum):
    """ユーザーの役割（権限レベル）"""
    ADMIN = "admin"          # 管理者: 全操作 + ユーザー管理
    OPERATOR = "operator"    # オペレーター: ロボット操作
    VIEWER = "viewer"        # 閲覧者: 読み取りのみ


# =============================================================================
# User エンティティ
# =============================================================================
#
# 【パスワードハッシュについて】
# パスワードは「平文」で保存してはいけない！
# もし DB が流出した場合、全ユーザーのパスワードが漏洩する。
#
# 代わりに「ハッシュ」を保存する:
#   password = "mypassword123"
#   hash = "$2b$12$LJ3.../..." (bcrypt ハッシュ)
#
# ハッシュから元のパスワードを復元するのは計算的に不可能。
# ログイン時は、入力されたパスワードをハッシュ化して比較する。
#
@dataclass
class User:
    """ユーザーエンティティ"""
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.VIEWER

    # --- 自動生成フィールド ---
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
