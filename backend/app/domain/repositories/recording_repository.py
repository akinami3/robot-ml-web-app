# ============================================================
# 録画セッションリポジトリインターフェース
# （Recording Repository Interface）
# ============================================================
# 録画セッション（センサーデータの記録単位）の保存・取得に
# 特化したリポジトリの「設計図」です。
#
# 録画セッション固有の操作：
# - アクティブな（進行中の）セッションの検索
# - セッションの停止処理
# - 統計情報（レコード数、サイズ）の更新
#
# 【1ロボット = 1セッション制約】
# 同時に1つのロボットについて1つの録画セッションしか実行できません。
# get_active_by_robot で現在アクティブなセッションを確認します。
# ============================================================
"""Recording session repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

# 録画セッションのエンティティ
from ..entities.recording import RecordingSession
from .base import BaseRepository


class RecordingRepository(BaseRepository[RecordingSession]):
    """
    録画セッションリポジトリの抽象インターフェース。

    録画の開始・停止・進行状況の管理メソッドを定義。
    """

    @abstractmethod
    async def get_active_by_robot(self, robot_id: UUID) -> RecordingSession | None:
        """
        指定ロボットのアクティブな（進行中の）録画セッションを取得する。
        1ロボットにつき同時に1セッションのみ許可するため、
        新規録画開始時にこのメソッドで重複チェックを行う。

        Args:
            robot_id: 確認するロボットのID
        Returns:
            アクティブなセッション、またはなければ None
        """
        ...

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID) -> list[RecordingSession]:
        """
        指定ユーザーのアクティブな録画セッション一覧を取得する。
        ユーザーは複数のロボットで同時に録画できる。

        Args:
            user_id: ユーザーのID
        Returns:
            アクティブなセッションのリスト
        """
        ...

    @abstractmethod
    async def get_by_robot(self, robot_id: UUID) -> list[RecordingSession]:
        """
        指定ロボットの全録画セッション（過去分も含む）を取得する。
        録画履歴の表示に使用。

        Args:
            robot_id: ロボットのID
        Returns:
            全セッションのリスト（アクティブ・停止済み両方）
        """
        ...

    @abstractmethod
    async def stop_session(self, session_id: UUID) -> bool:
        """
        録画セッションを停止する。
        is_active フラグを False に、stopped_at に現在時刻を設定。

        Args:
            session_id: 停止するセッションのID
        Returns:
            停止に成功したら True
        """
        ...

    @abstractmethod
    async def update_stats(
        self, session_id: UUID, record_count: int, size_bytes: int
    ) -> bool:
        """
        録画セッションの統計情報を更新する。
        録画中に定期的に（例: 100件ごとに）呼び出される。

        Args:
            session_id: セッションのID
            record_count: 現在のレコード数
            size_bytes: 現在のデータサイズ（バイト）
        Returns:
            更新に成功したら True
        """
        ...
