# ============================================================
# センサーデータリポジトリインターフェース
# （Sensor Data Repository Interface）
# ============================================================
# センサーデータの保存・取得に特化したリポジトリの「設計図」です。
#
# センサーデータは、他のエンティティと比べて以下の特徴があります：
# - データ量が非常に多い（1秒に数十〜数百件）
# - 時系列データである（時間の順序が重要）
# - 集計（平均・最大・最小）が必要になる
# - 古いデータの定期的な削除が必要
#
# そのため、以下の特殊なメソッドを追加定義しています：
# - 時間範囲でのフィルタリング
# - 一括挿入（bulk_insert）で高速化
# - 時間バケットでの集計（aggregated）
# - 古いデータの一括削除（delete_older_than）
# ============================================================
"""Sensor data repository interface."""

from __future__ import annotations

from abc import abstractmethod
# datetime: 日付と時刻を扱うクラス
from datetime import datetime
from uuid import UUID

# センサーデータのエンティティとセンサータイプの列挙型
from ..entities.sensor_data import SensorData, SensorType
from .base import BaseRepository


class SensorDataRepository(BaseRepository[SensorData]):
    """
    センサーデータリポジトリの抽象インターフェース。

    時系列データの効率的な保存・検索・集計のためのメソッドを定義。
    実装では TimescaleDB の hypertable 機能を活用します。
    """

    @abstractmethod
    async def get_by_robot(
        self,
        robot_id: UUID,
        # パイプ記法「型 | None」は「その型か None のどちらか」を意味します
        # None がデフォルト → 省略可能なパラメータ
        sensor_type: SensorType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[SensorData]:
        """
        ロボットIDを基にセンサーデータを検索する。
        オプションでセンサータイプや時間範囲でフィルタリング可能。

        Args:
            robot_id: データを取得するロボットのID
            sensor_type: フィルタするセンサーの種類（省略可）
            start_time: データ取得の開始時刻（省略可）
            end_time: データ取得の終了時刻（省略可）
            limit: 最大取得件数（デフォルト: 1000）
        Returns:
            条件に合うセンサーデータのリスト
        """
        ...

    @abstractmethod
    async def get_by_session(
        self,
        session_id: UUID,
        sensor_type: SensorType | None = None,
    ) -> list[SensorData]:
        """
        録画セッションIDに紐づくセンサーデータを取得する。
        データセット作成時に使用される。

        Args:
            session_id: 録画セッションのID
            sensor_type: フィルタするセンサーの種類（省略可）
        Returns:
            セッションに関連するセンサーデータのリスト
        """
        ...

    @abstractmethod
    async def bulk_insert(self, data: list[SensorData]) -> int:
        """
        複数のセンサーデータを一括挿入する（バルクインサート）。

        【なぜ一括挿入？】
        1件ずつINSERTすると、毎回データベースとの通信が発生して遅い。
        一括挿入なら1回の通信で数百件を保存でき、大幅に高速化できる。

        Args:
            data: 挿入するセンサーデータのリスト
        Returns:
            実際に挿入された件数
        """
        ...

    @abstractmethod
    async def get_latest(
        self, robot_id: UUID, sensor_type: SensorType
    ) -> SensorData | None:
        """
        指定ロボット・センサータイプの最新データを1件取得する。
        リアルタイムダッシュボードでの表示に使用。

        Args:
            robot_id: ロボットのID
            sensor_type: センサーの種類
        Returns:
            最新のセンサーデータ、またはデータがなければ None
        """
        ...

    @abstractmethod
    async def count_by_session(self, session_id: UUID) -> int:
        """
        録画セッションに含まれるデータの件数を取得する。

        Args:
            session_id: 録画セッションのID
        Returns:
            データの件数
        """
        ...

    @abstractmethod
    async def delete_older_than(self, before: datetime) -> int:
        """
        指定日時より古いデータを一括削除する。
        ストレージ容量の管理のため、定期的に実行される。

        Args:
            before: この日時より古いデータを削除
        Returns:
            削除された件数
        """
        ...

    @abstractmethod
    async def get_aggregated(
        self,
        robot_id: UUID,
        sensor_type: SensorType,
        start_time: datetime,
        end_time: datetime,
        bucket_seconds: int = 60,
    ) -> list[dict]:
        """
        時間バケット（一定間隔）ごとにデータを集計する。

        【時間バケットとは？】
        例: bucket_seconds=60 なら、1分ごとにデータをまとめて
        平均値・最大値・最小値・件数を計算します。
        TimescaleDB の time_bucket() 関数を使って高速に処理。

        グラフ表示で大量のデータポイントを間引くために使用。

        Args:
            robot_id: ロボットのID
            sensor_type: センサーの種類
            start_time: 集計開始時刻
            end_time: 集計終了時刻
            bucket_seconds: バケットの間隔（秒）。デフォルト60秒
        Returns:
            各バケットの集計結果（辞書のリスト）
            例: [{"time": ..., "avg": 25.3, "min": 24.1, "max": 26.5, "count": 60}]
        """
        ...
