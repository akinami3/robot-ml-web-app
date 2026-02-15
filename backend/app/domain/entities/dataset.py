"""
Dataset domain entity.
データセット ドメインエンティティ

このファイルでは、機械学習用の「データセット」を表現するデータ構造を定義しています。
データセットとは、ロボットのセンサーデータを集めてまとめたものです。
集めたデータはCSVやJSON形式でエクスポートして、機械学習のトレーニングに使用できます。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


# --- データセットの状態を表す列挙型 ---
class DatasetStatus(str, enum.Enum):
    """
    データセットの処理状態を表す列挙型。
    データセットは作成→準備完了→エクスポート→アーカイブという流れで状態が遷移します。
    """
    CREATING = "creating"     # 作成中: データを集めている最中
    READY = "ready"           # 準備完了: データ収集が完了し、利用可能な状態
    EXPORTING = "exporting"   # エクスポート中: CSV等の形式に変換中
    ARCHIVED = "archived"     # アーカイブ済み: 使い終わって保管された状態
    ERROR = "error"           # エラー: 何らかの問題が発生


# --- エクスポート形式を表す列挙型 ---
class DatasetExportFormat(str, enum.Enum):
    """
    データセットをファイルに出力する際の形式。
    機械学習で使う形式に応じて選択します。
    """
    CSV = "csv"           # CSV: カンマ区切りテキスト（Excel等で開ける、最も一般的）
    PARQUET = "parquet"   # Parquet: 列指向バイナリ形式（大規模データに高速）
    JSON = "json"         # JSON: JavaScriptオブジェクト記法（Web APIで一般的）
    ROSBAG = "rosbag"     # ROSBag: ROS（ロボットOS）のデータ形式（将来対応予定）
    HDF5 = "hdf5"         # HDF5: 階層データ形式（科学計算・深層学習で使用）


# --- データセットエンティティ（データクラス） ---
@dataclass
class Dataset:
    """
    機械学習用データセットを表すデータクラス。

    ロボットのセンサーデータを期間やセンサー種類で絞り込んで集めた
    データの集まりです。タグやメタデータで整理・検索できます。

    Attributes:
        name: データセットの名前（例: "リビング走行データ_20240101"）
        description: データセットの説明
        owner_id: 作成者のユーザーID
        id: データセットの一意なID
        status: 現在の処理状態
        sensor_types: 含まれるセンサーの種類リスト
        robot_ids: データを取得したロボットのIDリスト
        start_time: データ収集開始時刻
        end_time: データ収集終了時刻
        record_count: 含まれるデータレコード数
        size_bytes: データサイズ（バイト単位）
        tags: 検索用タグ（例: ["indoor", "lidar", "navigation"]）
        metadata: 追加情報（自由形式の辞書）
    """
    # --- 必須フィールド ---
    name: str           # データセット名
    description: str    # 説明
    owner_id: UUID      # 作成者のユーザーID

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)
    status: DatasetStatus = DatasetStatus.CREATING      # 初期状態は「作成中」
    sensor_types: list[str] = field(default_factory=list)   # センサー種類リスト
    robot_ids: list[UUID] = field(default_factory=list)     # ロボットIDリスト
    start_time: datetime | None = None                       # 収集開始時刻
    end_time: datetime | None = None                         # 収集終了時刻
    record_count: int = 0                                    # レコード数
    size_bytes: int = 0                                      # データサイズ（バイト）
    tags: list[str] = field(default_factory=list)            # タグリスト
    metadata: dict = field(default_factory=dict)             # 追加メタデータ
    created_at: datetime = field(default_factory=datetime.utcnow)   # 作成日時
    updated_at: datetime = field(default_factory=datetime.utcnow)   # 更新日時

    @property
    def is_exportable(self) -> bool:
        """
        このデータセットがエクスポート可能かどうかを判定するプロパティ。

        エクスポートするには2つの条件を同時に満たす必要があります:
        1. ステータスが READY（準備完了）であること
        2. レコード数が1件以上あること（空のデータセットはエクスポートしない）

        Python の and 演算子は、両方が True の場合のみ True を返します。
        """
        return self.status == DatasetStatus.READY and self.record_count > 0
