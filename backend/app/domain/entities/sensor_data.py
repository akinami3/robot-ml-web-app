"""
Sensor data domain entity.
センサーデータ ドメインエンティティ

このファイルでは、ロボットから取得する各種センサーデータを表現するデータ構造を定義しています。
LiDAR、カメラ、IMU、オドメトリなど様々なセンサーの種類を列挙型で管理し、
取得したデータをデータクラスにまとめています。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime

# Any: 任意の型を受け入れる型ヒント（センサーデータは種類によって形式が異なるため）
from typing import Any

from uuid import UUID, uuid4


# --- センサーの種類を表す列挙型 ---
# ロボットに搭載される各種センサーの種類を定義します
class SensorType(str, enum.Enum):
    """
    センサーの種類を表す列挙型。

    各センサーの特徴:
    - LIDAR: レーザー光で周囲360度の距離を測定（障害物回避や地図作成に使用）
    - CAMERA: RGB画像を取得（物体認識やナビゲーションに使用）
    - IMU: 加速度と角速度を3軸で測定（ロボットの姿勢推定に使用）
    - ODOMETRY: 車輪の回転から移動量を計算（位置推定に使用）
    - BATTERY: バッテリーの残量・電圧を監視
    - GPS: 衛星を使って地球上の位置（緯度・経度）を測定
    - POINT_CLOUD: 3Dの点群データ（3次元地図作成に使用）
    - JOINT_STATE: ロボットアームの各関節の角度
    """
    LIDAR = "lidar"
    CAMERA = "camera"
    IMU = "imu"
    ODOMETRY = "odometry"
    BATTERY = "battery"
    GPS = "gps"
    POINT_CLOUD = "point_cloud"
    JOINT_STATE = "joint_state"


# --- センサーデータエンティティ（データクラス） ---
@dataclass
class SensorData:
    """
    1回分のセンサー測定データを表すデータクラス。

    ロボットが取得したセンサーデータ1件（1スキャン分、1フレーム分）を表します。
    データの中身（data フィールド）はセンサーの種類によって異なります。

    例:
    - LiDARの場合: {"ranges": [1.2, 1.5, ...], "angle_min": -3.14, "angle_max": 3.14}
    - IMUの場合: {"linear_accel": {"x": 0.1, "y": 0.0, "z": 9.8}, "angular_vel": {...}}
    - バッテリーの場合: {"voltage": 12.4, "percentage": 85.0}

    Attributes:
        robot_id: このデータを取得したロボットのID
        sensor_type: センサーの種類
        data: センサーデータの中身（辞書形式、内容はセンサーによって異なる）
        id: このデータの一意なID
        timestamp: データ取得時刻
        session_id: 記録セッションのID（記録中の場合）
        sequence_number: データの通し番号（順序管理用）
    """
    # --- 必須フィールド ---
    robot_id: UUID              # どのロボットのデータか
    sensor_type: SensorType     # どの種類のセンサーか
    data: dict[str, Any]        # センサーデータの中身（JSON形式の辞書）

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)                    # データの一意なID
    timestamp: datetime = field(default_factory=datetime.utcnow)  # 取得時刻（UTC）
    session_id: UUID | None = None   # 記録セッションID（記録していない場合はNone）
    sequence_number: int = 0          # シーケンス番号（データの順番を管理）

    @property
    def is_image_type(self) -> bool:
        """
        このデータが画像データかどうかを判定するプロパティ。
        カメラデータのみが画像型です。画像データは他のデータと異なる表示・保存方法が必要です。
        """
        return self.sensor_type == SensorType.CAMERA

    @property
    def is_time_series(self) -> bool:
        """
        このデータが時系列データかどうかを判定するプロパティ。
        時系列データとは、時間の経過とともに連続的に変化する数値データです。
        グラフで表示するのに適しています（IMU、オドメトリ、バッテリー、GPS）。
        """
        return self.sensor_type in (
            SensorType.IMU,
            SensorType.ODOMETRY,
            SensorType.BATTERY,
            SensorType.GPS,
        )
