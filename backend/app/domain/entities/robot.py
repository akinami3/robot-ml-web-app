"""
Robot domain entity.
ロボットドメインエンティティ

このファイルでは、アプリケーションが管理する「ロボット」を表現するデータ構造を定義しています。
ロボットの状態（接続中、移動中、緊急停止など）や能力（LiDAR搭載、カメラ搭載など）を
列挙型で管理し、ロボットの情報をデータクラスにまとめています。
"""

from __future__ import annotations

# enum: 列挙型を作る標準ライブラリ
import enum

from dataclasses import dataclass, field
from datetime import datetime

# Any: どんな型でも受け入れられる特殊な型ヒント
# 例: dict[str, Any] は {"key": 123} でも {"key": "text"} でもOK
from typing import Any

from uuid import UUID, uuid4


# --- ロボットの状態を表す列挙型 ---
# ロボットが今どんな状態にあるかを表します（状態遷移図のノードに対応）
class RobotState(str, enum.Enum):
    """ロボットの接続・動作状態を表す列挙型"""
    DISCONNECTED = "disconnected"           # 切断状態: ロボットと通信できない
    CONNECTING = "connecting"               # 接続中: WebSocket接続を確立中
    IDLE = "idle"                           # 待機中: 接続済みだが動いていない
    MOVING = "moving"                       # 移動中: 速度コマンドを受けて動いている
    ERROR = "error"                         # エラー: 何らかの異常が発生
    EMERGENCY_STOPPED = "emergency_stopped" # 緊急停止: E-Stopが押された状態


# --- ロボットの能力（機能）を表す列挙型 ---
# ロボットにどんなセンサーや機能が搭載されているかを表します
class RobotCapability(str, enum.Enum):
    """ロボットが持つ機能・センサーの種類"""
    VELOCITY_CONTROL = "velocity_control"   # 速度制御: ロボットの移動速度を指定できる
    NAVIGATION = "navigation"               # 自律ナビゲーション: 目的地を指定して自動移動
    LIDAR = "lidar"                         # LiDAR: レーザーで周囲の距離を測定するセンサー
    CAMERA = "camera"                       # カメラ: 画像を取得するセンサー
    IMU = "imu"                             # IMU: 加速度・角速度を測定するセンサー
    ODOMETRY = "odometry"                   # オドメトリ: 車輪の回転から走行距離を推定
    BATTERY_MONITOR = "battery_monitor"     # バッテリー監視: 電池残量を確認
    GPS = "gps"                             # GPS: 地球上の位置を測定
    ARM_CONTROL = "arm_control"             # ロボットアーム制御: マニピュレータの操作


# --- ロボットエンティティ（データクラス） ---
@dataclass
class Robot:
    """
    ロボットを表すデータクラス。

    1台のロボットに対応し、接続情報・状態・搭載センサーなどを管理します。
    adapter_type は、どのロボットドライバ（アダプター）を使って通信するかを指定します。

    Attributes:
        name: ロボットの名前（表示用）
        adapter_type: 通信アダプターの種類（"mock", "ros2" など）
        id: ロボットの一意なID
        state: 現在の状態
        capabilities: 搭載している機能のリスト
        connection_params: 接続パラメータ（IPアドレス、ポートなど）
        battery_level: バッテリー残量（0.0〜100.0、未取得ならNone）
        last_seen: 最後に通信した日時
    """
    # --- 必須フィールド ---
    name: str                  # ロボットの表示名
    adapter_type: str          # アダプタータイプ（例: "mock", "ros2", "stretch"）

    # --- オプションフィールド ---
    id: UUID = field(default_factory=uuid4)                              # 一意なID
    state: RobotState = RobotState.DISCONNECTED                          # 初期状態は「切断」
    capabilities: list[RobotCapability] = field(default_factory=list)    # 搭載機能リスト
    connection_params: dict[str, Any] = field(default_factory=dict)      # 接続パラメータ
    battery_level: float | None = None                                    # バッテリー残量（%）
    last_seen: datetime | None = None                                     # 最終通信日時
    created_at: datetime = field(default_factory=datetime.utcnow)        # 作成日時
    updated_at: datetime = field(default_factory=datetime.utcnow)        # 更新日時

    @property
    def is_connected(self) -> bool:
        """
        ロボットが接続されているかどうかを判定するプロパティ。
        @property デコレータにより、メソッドだが robot.is_connected のように
        属性のようにアクセスできます（カッコ不要）。

        DISCONNECTEDとCONNECTING以外の状態なら「接続済み」と判定します。
        """
        return self.state not in (RobotState.DISCONNECTED, RobotState.CONNECTING)

    @property
    def is_emergency_stopped(self) -> bool:
        """
        緊急停止状態かどうかを判定するプロパティ。
        E-Stop（Emergency Stop）ボタンが押された状態です。
        """
        return self.state == RobotState.EMERGENCY_STOPPED
