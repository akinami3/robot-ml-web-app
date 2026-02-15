"""
User domain entity.
ユーザードメインエンティティ

このファイルでは、アプリケーションの「ユーザー」を表現するデータ構造を定義しています。
ドメインエンティティとは、ビジネスロジックの中心となるデータモデルのことです。
データベースやAPIとは独立した純粋なPythonクラスとして定義します（クリーンアーキテクチャ）。
"""

# --- 標準ライブラリのインポート ---
# from __future__ import annotations: Python 3.10+の型ヒント記法を古いバージョンでも使えるようにする
from __future__ import annotations

# enum: 列挙型（決まった選択肢の中から1つを選ぶ型）を作るためのモジュール
import enum

# dataclass: クラスの __init__ や __repr__ を自動生成してくれる便利なデコレータ
from dataclasses import dataclass, field

# datetime: 日時を扱うためのモジュール
from datetime import datetime

# UUID: 世界中で一意（ユニーク）なIDを生成するためのモジュール
# 例: "550e8400-e29b-41d4-a716-446655440000" のような文字列
from uuid import UUID, uuid4


# --- ユーザーの役割（ロール）を定義する列挙型 ---
# str と enum.Enum を両方継承することで、文字列としても扱える列挙型になります
# 例: UserRole.ADMIN == "admin" が True になる
class UserRole(str, enum.Enum):
    """ユーザーの権限レベルを表す列挙型"""
    ADMIN = "admin"          # 管理者: 全ての操作が可能
    OPERATOR = "operator"    # オペレーター: ロボット操作が可能
    VIEWER = "viewer"        # 閲覧者: データの閲覧のみ可能


# --- ユーザーエンティティ（データクラス） ---
# @dataclass デコレータにより、__init__ メソッドが自動生成されます
# つまり User(username="taro", email="taro@example.com", role=UserRole.VIEWER) のように作成できます
@dataclass
class User:
    """
    ユーザーを表すデータクラス。

    Attributes:
        username: ユーザー名（ログイン時に使用）
        email: メールアドレス
        role: ユーザーの役割（ADMIN/OPERATOR/VIEWER）
        hashed_password: ハッシュ化されたパスワード（平文では保存しない）
        id: ユーザーの一意なID（UUID形式で自動生成）
        is_active: アカウントが有効かどうか
        created_at: アカウント作成日時
        updated_at: 最終更新日時
    """
    # --- 必須フィールド（デフォルト値なし） ---
    username: str           # ユーザー名
    email: str              # メールアドレス
    role: UserRole          # ユーザーの権限レベル

    # --- オプションフィールド（デフォルト値あり） ---
    hashed_password: str = ""  # パスワードはハッシュ化して保存（セキュリティのため平文は保存しない）
    # field(default_factory=uuid4): 新しいインスタンスが作られるたびに新しいUUIDを生成
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True     # デフォルトでアカウントは有効
    created_at: datetime = field(default_factory=datetime.utcnow)   # 作成日時（UTC）
    updated_at: datetime = field(default_factory=datetime.utcnow)   # 更新日時（UTC）

    def can_control_robot(self) -> bool:
        """
        ロボットを操作できるかどうかを判定するメソッド。
        管理者（ADMIN）またはオペレーター（OPERATOR）のみロボット操作が可能です。

        Returns:
            bool: ロボット操作が可能なら True
        """
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR)

    def can_manage_users(self) -> bool:
        """
        ユーザー管理ができるかどうかを判定するメソッド。
        管理者（ADMIN）のみがユーザーの追加・削除などを行えます。

        Returns:
            bool: ユーザー管理が可能なら True
        """
        return self.role == UserRole.ADMIN

    def can_view_data(self) -> bool:
        """
        データの閲覧ができるかどうかを判定するメソッド。
        全てのユーザーがデータを閲覧できます。

        Returns:
            bool: 常に True（全ロールで閲覧可能）
        """
        return True
