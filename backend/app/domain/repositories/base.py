# =============================================================================
# Step 7: ベースリポジトリ — 抽象基底クラス
# =============================================================================
#
# 【リポジトリパターンとは？】
# データアクセスのインターフェースを定義するデザインパターン。
# 実装の詳細（SQL, ファイル, メモリなど）を隠蔽する。
#
#   API 層:     robot_repo.list_all() を呼ぶ
#   ドメイン層:  RobotRepository (インターフェース) を定義
#   インフラ層:  SQLAlchemyRobotRepository がSQL を実行
#
# 利点:
#   1. テスト時にモックリポジトリに差し替えられる
#   2. DB を PostgreSQL → MongoDB に変えても、ドメイン層は影響なし
#   3. 関心の分離（API はDBの種類を知らない）
#
# 【ABC (Abstract Base Class) とは？】
# 抽象基底クラス。インスタンス化できないクラス。
# サブクラスに「このメソッドを必ず実装してね」と強制する。
#
# Go との比較:
#   Go:     type RobotRepository interface { ListAll() ([]Robot, error) }
#   Python: class RobotRepository(ABC): @abstractmethod async def list_all() -> list[Robot]
#
# Go は暗黙的インターフェース実装（構造体がメソッドを持てば自動実装）。
# Python は明示的に ABC を継承する必要がある。
#
# 【Generic（ジェネリクス）とは？】
# 型パラメータ（T）を使って、どの型でも使える汎用クラスを作る仕組み。
#
#   BaseRepository[Robot]  → T が Robot になる
#   BaseRepository[User]   → T が User になる
#
# Go との比較:
#   Go:     type BaseRepository[T any] interface { ... }
#   Python: class BaseRepository(ABC, Generic[T]): ...
#
# =============================================================================

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

# --- 型変数 T ---
# T は「任意のエンティティ型」を表す。
# BaseRepository[Robot] と書くと、T = Robot として型チェックが行われる。
T = TypeVar("T")


# =============================================================================
# BaseRepository — 汎用リポジトリインターフェース
# =============================================================================
class BaseRepository(ABC, Generic[T]):
    """
    ベースリポジトリ抽象クラス

    全エンティティ共通の CRUD 操作を定義する。
    具体的な実装はインフラ層のサブクラスが行う。
    """

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> T | None:
        """
        ID でエンティティを1件取得する

        見つからない場合は None を返す（例外は投げない）。
        「見つからない」は正常ケースのため。
        """
        ...

    @abstractmethod
    async def list_all(self) -> list[T]:
        """全エンティティを取得する"""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        エンティティを作成する

        Returns: 作成されたエンティティ（ID が確定した状態）
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        エンティティを更新する

        Returns: 更新されたエンティティ
        Raises: ValueError: エンティティが存在しない場合
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        エンティティを削除する

        Returns: True = 削除成功, False = 見つからなかった
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """エンティティの総数を取得する"""
        ...
