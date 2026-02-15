# ============================================================
# ユーザーリポジトリインターフェース（User Repository Interface）
# ============================================================
# ユーザーデータの保存・取得に特化したリポジトリの「設計図」です。
#
# BaseRepository[User] を継承しているので、
# CRUD操作（get_by_id, get_all, create, update, delete, count）は
# 既に定義済み。ここではユーザー固有の追加メソッドを定義します。
#
# 【なぜインターフェースと実装を分けるのか？】
# - テスト時にモック（偽の実装）を使える
# - データベースを変更しても、ビジネスロジックを変更しなくてよい
# - 依存関係の方向を制御できる（依存性逆転の原則: DIP）
# ============================================================
"""User repository interface."""

from __future__ import annotations

# abstractmethod: 子クラスで必ず実装させるためのデコレータ
from abc import abstractmethod

# User エンティティ（ドメインオブジェクト）をインポート
from ..entities.user import User
# 共通のCRUD操作を持つベースリポジトリ
from .base import BaseRepository


# BaseRepository[User] → T が User に置き換わる
# つまり get_by_id は User | None を、get_all は list[User] を返す
class UserRepository(BaseRepository[User]):
    """
    ユーザーリポジトリの抽象インターフェース。

    BaseRepository の CRUD に加えて、ユーザー固有の検索メソッドを定義。
    実際のデータベース操作は infrastructure 層の実装クラスが担当します。
    """

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """
        ユーザー名でユーザーを検索する。
        ログイン時の認証で使用される重要なメソッド。

        Args:
            username: 検索するユーザー名
        Returns:
            見つかったユーザー、または None
        """
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """
        メールアドレスでユーザーを検索する。
        ユーザー登録時の重複チェックで使用。

        Args:
            email: 検索するメールアドレス
        Returns:
            見つかったユーザー、または None
        """
        ...

    @abstractmethod
    async def get_active_users(self) -> list[User]:
        """
        アクティブな（有効な）ユーザーの一覧を取得する。
        is_active が True のユーザーのみを返す。

        Returns:
            アクティブなユーザーのリスト
        """
        ...
