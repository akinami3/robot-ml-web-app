# ============================================================
# ベースリポジトリインターフェース（Base Repository Interface）
# ============================================================
# このファイルは、すべてのリポジトリ（データ保存/取得の窓口）が
# 共通して持つべきメソッドを定義する「抽象基底クラス」です。
#
# 【リポジトリパターンとは？】
# リポジトリパターンは、データベースへのアクセスを抽象化するデザインパターンです。
# ビジネスロジック（ドメイン層）はデータベースの種類（PostgreSQL, MySQL等）を
# 知る必要がなく、このインターフェースだけを使います。
#
# 【抽象基底クラス (ABC) とは？】
# ABC = Abstract Base Class の略。このクラス自体はインスタンス化できず、
# 継承した子クラスが必ず全てのメソッドを実装する必要があります。
# → 「設計図」のようなもので、実装の強制ができます。
#
# 【CRUD操作】
# Create（作成）、Read（読み取り）、Update（更新）、Delete（削除）
# の4つの基本操作を定義しています。
# ============================================================
"""Base repository interface."""

from __future__ import annotations

# abc: 抽象基底クラス（Abstract Base Class）を作るためのモジュール
from abc import ABC, abstractmethod
# typing: 型ヒントのためのモジュール
# Any: どんな型でもOK、Generic: 型パラメータを使えるようにする、TypeVar: 型変数を定義
from typing import Any, Generic, TypeVar
# UUID: ユニバーサルユニークID（重複しない一意の識別子）
from uuid import UUID

# TypeVar("T") は「型変数」を定義します
# T は「どんな型でも入る箱」のようなもの
# 例: BaseRepository[User] とすると、T = User になります
T = TypeVar("T")


# Generic[T] を継承することで、このクラスは「ジェネリッククラス」になります
# → 使う側が型を指定できる: BaseRepository[User], BaseRepository[Robot] など
class BaseRepository(ABC, Generic[T]):
    """
    全てのリポジトリが実装すべき共通メソッドを定義する抽象基底クラス。

    Generic[T] により、エンティティの型をパラメータとして受け取ります。
    例: BaseRepository[User] → get_by_id() は User | None を返す
    """

    @abstractmethod  # このデコレータで「子クラスで必ず実装してね」と強制する
    async def get_by_id(self, id: UUID) -> T | None:
        """
        IDでエンティティを1件取得する。
        見つからなければ None を返す。

        Args:
            id: 検索するエンティティのUUID
        Returns:
            見つかったエンティティ、または None
        """
        ...  # 「...」は「実装は子クラスに任せる」という意味（pass と同じ）

    @abstractmethod
    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """
        全エンティティを一覧取得する（ページネーション対応）。

        Args:
            offset: 何件目から取得するか（デフォルト: 0 = 最初から）
            limit: 最大何件取得するか（デフォルト: 100件）
        Returns:
            エンティティのリスト
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        新しいエンティティを作成（データベースに保存）する。

        Args:
            entity: 保存するエンティティオブジェクト
        Returns:
            保存されたエンティティ（IDが付与された状態）
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        既存のエンティティを更新する。

        Args:
            entity: 更新するエンティティオブジェクト
        Returns:
            更新されたエンティティ
        """
        ...

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """
        IDを指定してエンティティを削除する。

        Args:
            id: 削除するエンティティのUUID
        Returns:
            削除に成功したら True、見つからなければ False
        """
        ...

    @abstractmethod
    async def count(self) -> int:
        """
        エンティティの総数を返す。

        Returns:
            データベースに保存されているエンティティの件数
        """
        ...
