"""
Recording session domain entity.
記録セッション ドメインエンティティ

このファイルでは、ロボットのセンサーデータを記録する「セッション」を表現する
データ構造を定義しています。

記録の流れ:
1. ユーザーが記録設定（どのセンサーを、どの頻度で記録するか）を作成
2. 記録セッションを開始（RecordingSession を作成）
3. センサーデータがリアルタイムで記録される
4. ユーザーが記録を停止（stop()メソッドを呼ぶ）
5. 記録されたデータをデータセットに変換して機械学習に利用
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

# 同じパッケージ内の sensor_data.py から SensorType をインポート
# 「.」は「同じディレクトリの」という意味（相対インポート）
from .sensor_data import SensorType


# --- 記録設定（コンフィグ）データクラス ---
@dataclass
class RecordingConfig:
    """
    記録セッションの設定を表すデータクラス。

    どのセンサーを、どの頻度で記録するかを指定します。
    ユーザーがUIから記録条件を設定する際に使用されます。

    Attributes:
        sensor_types: 記録対象のセンサー種類リスト（空リスト=全センサー）
        max_frequency_hz: センサー毎の最大記録頻度（Hz = 1秒あたりの回数）
        enabled: この設定が有効かどうか
    """
    # 記録するセンサーの種類リスト（空 = 全センサーを記録）
    sensor_types: list[SensorType] = field(default_factory=list)
    # センサー毎の最大記録頻度（例: {SensorType.LIDAR: 10.0} → LiDARは秒間10回まで）
    max_frequency_hz: dict[SensorType, float] = field(default_factory=dict)
    # この設定が有効かどうか
    enabled: bool = True

    def is_sensor_enabled(self, sensor_type: SensorType) -> bool:
        """
        指定されたセンサーが記録対象かどうかを判定するメソッド。

        Args:
            sensor_type: チェックしたいセンサーの種類

        Returns:
            bool: 記録対象ならTrue

        ロジック:
        1. 設定自体が無効（enabled=False）なら、全センサー記録しない
        2. sensor_types が空リストなら、全センサーを記録する
        3. sensor_types にセンサーが含まれていれば記録する
        """
        if not self.enabled:
            return False
        if not self.sensor_types:
            return True  # 空リスト = 全センサーが対象
        return sensor_type in self.sensor_types

    def get_max_frequency(self, sensor_type: SensorType) -> float | None:
        """
        指定されたセンサーの最大記録頻度を取得するメソッド。

        Args:
            sensor_type: 頻度を取得したいセンサーの種類

        Returns:
            float | None: 最大頻度（Hz）。設定されていない場合はNone（制限なし）

        dict.get() メソッドは、キーが存在しない場合にNoneを返します（KeyErrorにならない）。
        """
        return self.max_frequency_hz.get(sensor_type)


# --- 記録セッションエンティティ ---
@dataclass
class RecordingSession:
    """
    1回の記録セッションを表すデータクラス。

    記録開始から停止までの1回分のセッション情報を管理します。

    Attributes:
        robot_id: 記録対象のロボットID
        user_id: 記録を開始したユーザーID
        config: 記録設定
        id: セッションの一意なID
        is_active: 現在記録中かどうか
        record_count: 記録されたデータ件数
        size_bytes: 記録データの合計サイズ（バイト）
        started_at: 記録開始日時
        stopped_at: 記録停止日時（記録中はNone）
        dataset_id: このセッションから作成されたデータセットのID
    """
    # --- 必須フィールド ---
    robot_id: UUID              # 記録対象のロボット
    user_id: UUID               # 記録を開始したユーザー
    config: RecordingConfig     # 記録設定

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True      # デフォルトは「記録中」
    record_count: int = 0       # 記録件数（記録中に増えていく）
    size_bytes: int = 0         # データサイズ
    started_at: datetime = field(default_factory=datetime.utcnow)   # 開始日時
    stopped_at: datetime | None = None   # 停止日時（記録中はNone）
    dataset_id: UUID | None = None       # 紐付けられたデータセットID

    def stop(self) -> None:
        """
        記録セッションを停止するメソッド。

        セッションの状態を変更します:
        1. is_active を False に設定（記録終了）
        2. stopped_at に現在時刻を記録（停止時間の記録）

        このように状態を変更するメソッドをドメインエンティティに
        持たせることで、ビジネスロジックがエンティティ内に閉じ込められます。
        """
        self.is_active = False
        self.stopped_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> float | None:
        """
        記録時間（秒）を計算するプロパティ。

        Returns:
            float | None: 記録時間（秒数）

        - 記録中の場合: 開始時刻から現在時刻までの経過時間
        - 停止済みの場合: 開始時刻から停止時刻までの時間

        datetime の引き算で timedelta オブジェクトが返り、
        .total_seconds() で秒数に変換しています。
        """
        if self.stopped_at is None:
            # 記録中: 現在時刻までの経過時間を計算
            return (datetime.utcnow() - self.started_at).total_seconds()
        # 停止済み: 開始〜停止の時間を計算
        return (self.stopped_at - self.started_at).total_seconds()
