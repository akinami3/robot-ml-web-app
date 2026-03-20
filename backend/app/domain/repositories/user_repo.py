# =============================================================================
# Step 8: ユーザーリポジトリ — ドメインインターフェース
# =============================================================================
#
# Robot リポジトリと同じパターン。
# 抽象インターフェースを定義し、インフラ層で実装する。
#
# =============================================================================

from abc import abstractmethod
from uuid import UUID

from app.domain.entities.user import User
from app.domain.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    ユーザーリポジトリのインターフェース

    BaseRepository の CRUD メソッドに加えて、
    認証で必要な検索メソッドを追加する。
    """

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """ユーザー名で検索（ログイン時に使用）"""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """メールアドレスで検索（重複チェックに使用）"""
        ...
