# ============================================================
# データセットリポジトリインターフェース
# （Dataset Repository Interface）
# ============================================================
# データセット（機械学習用のデータ集合）の保存・取得に
# 特化したリポジトリの「設計図」です。
#
# データセット固有の操作：
# - オーナー（作成者）で検索
# - ステータス（作成中/準備完了/エクスポート中）で検索
# - ステータスの更新
# - 統計情報（レコード数、サイズ）の更新
# - タグ（ラベル）による検索
# ============================================================
"""Dataset repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

# データセットのエンティティとステータス列挙型
from ..entities.dataset import Dataset, DatasetStatus
from .base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """
    データセットリポジトリの抽象インターフェース。

    データセットの検索・ステータス管理・統計更新のメソッドを定義。
    """

    @abstractmethod
    async def get_by_owner(self, owner_id: UUID) -> list[Dataset]:
        """
        オーナー（作成者）IDでデータセットを検索する。
        ユーザーは自分が作成したデータセットのみ表示する。

        Args:
            owner_id: データセット作成者のユーザーID
        Returns:
            該当するデータセットのリスト
        """
        ...

    @abstractmethod
    async def get_by_status(self, status: DatasetStatus) -> list[Dataset]:
        """
        ステータス（状態）でデータセットを検索する。
        例: DatasetStatus.READY で利用可能なデータセットを取得。

        Args:
            status: フィルタするステータス
        Returns:
            該当するデータセットのリスト
        """
        ...

    @abstractmethod
    async def update_status(self, dataset_id: UUID, status: DatasetStatus) -> bool:
        """
        データセットのステータスを更新する（部分更新）。

        ステータスの遷移例:
        CREATING → READY（作成完了）
        READY → EXPORTING（エクスポート中）
        EXPORTING → READY（エクスポート完了）

        Args:
            dataset_id: 更新するデータセットのID
            status: 新しいステータス
        Returns:
            更新に成功したら True
        """
        ...

    @abstractmethod
    async def update_stats(
        self, dataset_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        """
        データセットの統計情報を更新する。
        データセット作成時にレコード数とサイズを計算して保存する。

        Args:
            dataset_id: 更新するデータセットのID
            record_count: データセットに含まれるレコード数
            size_bytes: データセットのサイズ（バイト単位）
        Returns:
            更新に成功したら True
        """
        ...

    @abstractmethod
    async def search_by_tags(self, tags: list[str]) -> list[Dataset]:
        """
        タグ（ラベル）でデータセットを検索する。
        例: ["lidar", "outdoor"] で屋外LiDARデータを検索。

        Args:
            tags: 検索するタグのリスト
        Returns:
            指定タグを含むデータセットのリスト
        """
        ...
