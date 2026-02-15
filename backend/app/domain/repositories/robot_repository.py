# ============================================================
# ロボットリポジトリインターフェース（Robot Repository Interface）
# ============================================================
# ロボットデータの保存・取得に特化したリポジトリの「設計図」です。
#
# ロボット固有の操作として、以下を追加定義しています：
# - 名前で検索
# - 状態（IDLE/ACTIVE/ERROR等）でフィルタリング
# - 状態の更新（部分更新）
# - バッテリー残量の更新（部分更新）
#
# 【部分更新とは？】
# エンティティ全体を更新する update() とは異なり、
# 特定のフィールドだけを効率的に更新する手法です。
# バッテリー残量やロボットの状態は頻繁に変わるため、
# 毎回全フィールドを更新するのは無駄が多いのです。
# ============================================================
"""Robot repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

# Robot エンティティと RobotState 列挙型をインポート
from ..entities.robot import Robot, RobotState
from .base import BaseRepository


class RobotRepository(BaseRepository[Robot]):
    """
    ロボットリポジトリの抽象インターフェース。

    ロボットの検索・状態管理に特化したメソッドを追加定義。
    """

    @abstractmethod
    async def get_by_name(self, name: str) -> Robot | None:
        """
        ロボット名でロボットを検索する。
        名前はユニーク（重複不可）なので、1件だけ返す。

        Args:
            name: 検索するロボット名
        Returns:
            見つかったロボット、または None
        """
        ...

    @abstractmethod
    async def get_by_state(self, state: RobotState) -> list[Robot]:
        """
        指定した状態のロボット一覧を取得する。
        例: RobotState.ACTIVE で現在稼働中のロボットを取得。

        Args:
            state: フィルタリングする状態（IDLE, ACTIVE, ERROR 等）
        Returns:
            該当する状態のロボットのリスト
        """
        ...

    @abstractmethod
    async def update_state(self, robot_id: UUID, state: RobotState) -> bool:
        """
        ロボットの状態だけを更新する（部分更新）。
        全フィールドの更新より効率的。

        Args:
            robot_id: 更新するロボットのID
            state: 新しい状態
        Returns:
            更新に成功したら True
        """
        ...

    @abstractmethod
    async def update_battery(self, robot_id: UUID, level: float) -> bool:
        """
        ロボットのバッテリー残量だけを更新する（部分更新）。
        バッテリー情報はセンサーから頻繁に更新されるため、
        専用メソッドで効率的に処理する。

        Args:
            robot_id: 更新するロボットのID
            level: バッテリー残量（0.0〜100.0 の範囲）
        Returns:
            更新に成功したら True
        """
        ...
