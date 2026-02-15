# ============================================================
# データセットサービス（Dataset Service）
# ============================================================
# データセット（機械学習用データ集合）の作成・管理・エクスポートに
# 関するビジネスロジックを担当するサービスクラスです。
#
# 【データセット作成の流れ】
# 1. ユーザーがロボットID、センサータイプ、時間範囲を指定
# 2. サービスが該当するセンサーデータを集計
# 3. データセットエンティティを作成し、統計情報を計算
# 4. ステータスを CREATING → READY に更新
#
# 【エクスポート機能】
# データセットを JSON/CSV/Parquet 形式でファイルに出力する機能。
# ステータスを READY → EXPORTING → READY と遷移させる。
# ============================================================
"""Dataset service - domain logic for dataset management."""

from __future__ import annotations

import structlog
from datetime import datetime
from uuid import UUID

# データセット関連のエンティティ（ドメインオブジェクト）
from ..entities.dataset import Dataset, DatasetExportFormat, DatasetStatus
# センサータイプの列挙型（LiDAR, IMU, カメラ等）
from ..entities.sensor_data import SensorType
# リポジトリのインターフェース（抽象クラス）
from ..repositories.dataset_repository import DatasetRepository
from ..repositories.sensor_data_repository import SensorDataRepository

logger = structlog.get_logger()


class DatasetService:
    """
    データセットに関するビジネスロジックを提供するサービスクラス。

    2つのリポジトリに依存：
    - DatasetRepository: データセットの保存・取得
    - SensorDataRepository: センサーデータの検索（データセット作成時に使用）
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        sensor_data_repo: SensorDataRepository,
    ) -> None:
        """
        コンストラクタ。2つのリポジトリを依存性注入で受け取る。

        Args:
            dataset_repo: データセットリポジトリ
            sensor_data_repo: センサーデータリポジトリ
        """
        self._dataset_repo = dataset_repo
        self._sensor_data_repo = sensor_data_repo

    async def create_dataset(
        self,
        name: str,
        description: str,
        owner_id: UUID,
        robot_ids: list[UUID],
        sensor_types: list[str],
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        tags: list[str] | None = None,
    ) -> Dataset:
        """
        新しいデータセットを作成する。

        【処理の流れ】
        ステップ1: データセットエンティティを作成（ステータス: CREATING）
        ステップ2: 該当するセンサーデータの件数を集計
        ステップ3: 統計情報（件数・サイズ）を更新
        ステップ4: ステータスを READY に更新

        Args:
            name: データセット名
            description: 説明文
            owner_id: 作成者のユーザーID
            robot_ids: 対象ロボットのIDリスト（複数ロボット対応）
            sensor_types: 対象センサータイプのリスト（文字列形式）
            start_time: データ収集の開始時刻（省略可）
            end_time: データ収集の終了時刻（省略可）
            tags: タグ（ラベル）のリスト（省略可）
        Returns:
            作成されたデータセット
        """
        # ステップ1: データセットエンティティを作成（初期ステータス: CREATING）
        dataset = Dataset(
            name=name,
            description=description,
            owner_id=owner_id,
            robot_ids=robot_ids,
            sensor_types=sensor_types,
            start_time=start_time,
            end_time=end_time,
            tags=tags or [],  # None の場合は空リストを使用
            status=DatasetStatus.CREATING,  # 「作成中」ステータス
        )
        created = await self._dataset_repo.create(dataset)

        # ステップ2: 該当するセンサーデータの件数を集計
        # 全ロボット × 全センサータイプ の組み合わせでデータ数を合計する
        count = 0
        for robot_id in robot_ids:
            for st_str in sensor_types:
                try:
                    # 文字列をSensorType列挙型に変換
                    st = SensorType(st_str)
                except ValueError:
                    # 無効なセンサータイプはスキップ
                    continue
                # 該当するセンサーデータを取得して件数をカウント
                data = await self._sensor_data_repo.get_by_robot(
                    robot_id=robot_id,
                    sensor_type=st,
                    start_time=start_time,
                    end_time=end_time,
                    limit=1_000_000,  # Python では _ で桁区切り可能（100万）
                )
                count += len(data)

        # ステップ3: 統計情報を更新（レコード数とサイズ）
        await self._dataset_repo.update_stats(created.id, count, 0)
        # ステップ4: ステータスを「準備完了」に更新
        await self._dataset_repo.update_status(created.id, DatasetStatus.READY)

        # 構造化ログに記録
        logger.info(
            "dataset_created",
            dataset_id=str(created.id),
            name=name,
            record_count=count,
        )
        # 最新の状態を取得して返す（ステータスが READY に更新されている）
        return await self._dataset_repo.get_by_id(created.id)  # type: ignore

    async def get_user_datasets(self, owner_id: UUID) -> list[Dataset]:
        """
        ユーザーが所有するデータセット一覧を取得する。

        Args:
            owner_id: データセット所有者のID
        Returns:
            データセットのリスト
        """
        return await self._dataset_repo.get_by_owner(owner_id)

    async def get_dataset(self, dataset_id: UUID) -> Dataset | None:
        """
        データセットを1件取得する。

        Args:
            dataset_id: データセットのID
        Returns:
            データセット、またはなければ None
        """
        return await self._dataset_repo.get_by_id(dataset_id)

    async def delete_dataset(self, dataset_id: UUID) -> bool:
        """
        データセットを削除する。

        Args:
            dataset_id: 削除するデータセットのID
        Returns:
            削除に成功したら True
        """
        return await self._dataset_repo.delete(dataset_id)

    async def export_dataset(
        self, dataset_id: UUID, format: DatasetExportFormat
    ) -> str:
        """
        データセットを指定形式でファイルにエクスポートする。

        【ステータスの遷移】
        READY → EXPORTING（エクスポート開始）
             → READY（エクスポート完了、元に戻す）

        Args:
            dataset_id: エクスポートするデータセットのID
            format: 出力形式（JSON, CSV, Parquet）
        Returns:
            エクスポートファイルのパス
        Raises:
            ValueError: データセットが見つからない、またはエクスポート不可の場合
        """
        # データセットの存在確認
        dataset = await self._dataset_repo.get_by_id(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        # エクスポート可能か確認（ステータスがREADYの場合のみ可能）
        if not dataset.is_exportable:
            raise ValueError(f"Dataset {dataset_id} is not exportable")

        # ステータスを「エクスポート中」に変更
        await self._dataset_repo.update_status(dataset_id, DatasetStatus.EXPORTING)

        # 全ロボット × 全センサータイプ のデータを収集
        all_data = []
        for robot_id in dataset.robot_ids:
            for st_str in dataset.sensor_types:
                try:
                    st = SensorType(st_str)
                except ValueError:
                    continue
                data = await self._sensor_data_repo.get_by_robot(
                    robot_id=robot_id,
                    sensor_type=st,
                    start_time=dataset.start_time,
                    end_time=dataset.end_time,
                    limit=1_000_000,
                )
                all_data.extend(data)  # extend: リストの末尾に複数要素を追加

        # エクスポートファイルのパス（実際にはフォーマット変換処理が入る）
        export_path = f"/tmp/exports/{dataset_id}.{format.value}"
        # TODO: ここに実際のフォーマット変換ロジックを実装
        # JSON → json.dumps(), CSV → csv.writer, Parquet → pandas.to_parquet() 等

        logger.info(
            "dataset_exported",
            dataset_id=str(dataset_id),
            format=format.value,
            records=len(all_data),
        )

        # ステータスを「準備完了」に戻す
        await self._dataset_repo.update_status(dataset_id, DatasetStatus.READY)
        return export_path
