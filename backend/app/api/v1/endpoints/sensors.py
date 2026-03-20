"""Sensor data endpoints."""
# ===========================================================
# センサーデータ API エンドポイント
# ===========================================================
# このファイルでは、ロボットのセンサーデータを取得・検索する
# ためのAPIエンドポイントを定義しています。
#
# 主な機能:
#   - センサーデータの検索（フィルタリング付き）
#   - 最新のセンサーデータの取得（最新データの取得）
#   - 集約データの取得（TimescaleDB time_bucket概念）
#   - センサータイプ一覧の取得
#
# センサーデータとは？
#   ロボットに搭載されたセンサー（カメラ、LiDAR、IMUなど）
#   から取得される計測データのことです。
# ===========================================================

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

# --- ドメイン層からセンサータイプの定義をインポート ---
# SensorType: センサーの種類を表すEnum（列挙型）
#   例: "camera", "lidar", "imu" など
from ....domain.entities.sensor_data import SensorType

# --- 依存性注入（DI）で使う型をインポート ---
# CurrentUser: ログイン中のユーザー情報（認証チェック用）
# SensorDataRepo: センサーデータのリポジトリ（データベース操作を担当）
from ..dependencies import CurrentUser, SensorDataRepo

# --- リクエスト/レスポンスのスキーマをインポート ---
# AggregatedDataQuery: 集約データ検索用のリクエストボディ
# SensorDataQuery: センサーデータ検索用のクエリ条件
# SensorDataResponse: センサーデータのレスポンス形式
from ..schemas import AggregatedDataQuery, SensorDataQuery, SensorDataResponse

# ---------------------------------------------------------
# ルーターの作成
# ---------------------------------------------------------
# prefix="/sensors" → すべてのエンドポイントが /sensors で始まる
# tags=["sensors"] → Swagger UIでグループ化して表示される
router = APIRouter(prefix="/sensors", tags=["sensors"])


# =============================================================
# センサーデータ検索エンドポイント
# =============================================================
# GET /sensors/data
#
# 指定したロボットのセンサーデータを検索して返します。
# クエリパラメータでフィルタリング条件を指定できます。
#
# 【クエリパラメータ】（URLの?以降に指定する値）
#   - robot_id: 対象ロボットのID（UUID形式、必須）
#   - sensor_type: センサーの種類（文字列、省略可能）
#   - limit: 取得件数の上限（デフォルト: 100件）
#
# 使用例:
#   GET /sensors/data?robot_id=xxx&sensor_type=lidar&limit=50
# =============================================================
@router.get("/data", response_model=list[SensorDataResponse])
async def query_sensor_data(
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
    robot_id: UUID,
    sensor_type: str | None = None,  # Noneならすべてのセンサータイプを対象にする
    limit: int = 100,                # 最大取得件数（デフォルト100件）
):
    # --- SensorType Enumのバリデーション（入力値の検証） ---
    # try/exceptパターンを使って、文字列をEnumに変換します。
    # もし無効な値（例: "invalid_sensor"）が渡された場合、
    # ValueErrorが発生するのでキャッチしてHTTP 400エラーを返します。
    #
    # 【ポイント】PythonのEnumの使い方:
    #   SensorType("lidar")  → SensorType.LIDAR  ✓ 有効な値
    #   SensorType("xxx")    → ValueError発生     ✗ 無効な値
    st = None
    if sensor_type:
        try:
            st = SensorType(sensor_type)
        except ValueError:
            # 不正なセンサータイプが指定された → 400 Bad Requestエラーを返す
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sensor type: {sensor_type}",
            )

    # リポジトリ経由でデータベースからセンサーデータを取得
    # sensor_type=Noneの場合はフィルタなし（全タイプ取得）
    data = await sensor_repo.get_by_robot(
        robot_id=robot_id,
        sensor_type=st,
        limit=limit,
    )

    # --- リスト内包表記でレスポンス変換 ---
    # データベースから取得したドメインエンティティ（内部データ構造）を
    # APIレスポンス用のスキーマ（外部データ構造）に変換しています。
    #
    # 【リスト内包表記の読み方】
    #   [変換処理(d) for d in data]
    #   → dataの各要素dに対して変換処理を行い、新しいリストを作成
    #
    # 【なぜ変換が必要？】
    #   ドメインエンティティ: アプリ内部の表現（sensor_typeはEnum型）
    #   レスポンススキーマ: API利用者向けの表現（sensor_typeは文字列）
    return [
        SensorDataResponse(
            id=d.id,
            robot_id=d.robot_id,
            sensor_type=d.sensor_type.value,  # Enum → 文字列に変換（例: SensorType.LIDAR → "lidar"）
            data=d.data,
            timestamp=d.timestamp,
            session_id=d.session_id,
            sequence_number=d.sequence_number,
        )
        for d in data
    ]


# =============================================================
# 最新センサーデータ取得エンドポイント（最新データの取得）
# =============================================================
# GET /sensors/data/latest
#
# 指定したロボット・センサータイプの「最新の1件」を取得します。
# ダッシュボードなどでリアルタイムの状態を表示する際に使います。
#
# 【最新データの取得パターン】
#   データがない場合はNoneを返し、HTTPレスポンスとしてもnullになります。
#   → フロントエンドでは「データなし」と表示すればOK
#
# 戻り値:
#   - データあり → SensorDataResponse（1件）
#   - データなし → None（null）
# =============================================================
@router.get("/data/latest", response_model=SensorDataResponse | None)
async def get_latest_sensor_data(
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
    robot_id: UUID,
    sensor_type: str,  # ここでは必須パラメータ（最新データは1種類ずつ取得する）
):
    # SensorType Enumのバリデーション（try/exceptパターン）
    try:
        st = SensorType(sensor_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensor type: {sensor_type}",
        )

    # 最新の1件を取得（なければNoneが返る）
    data = await sensor_repo.get_latest(robot_id, st)
    if data is None:
        # データが見つからなかった場合 → Noneを返す（エラーではない）
        return None

    # ドメインエンティティ → レスポンススキーマに変換して返す
    return SensorDataResponse(
        id=data.id,
        robot_id=data.robot_id,
        sensor_type=data.sensor_type.value,
        data=data.data,
        timestamp=data.timestamp,
        session_id=data.session_id,
        sequence_number=data.sequence_number,
    )


# =============================================================
# 集約（アグリゲーション）データ取得エンドポイント
# =============================================================
# POST /sensors/data/aggregated
#
# 時系列データを時間単位でまとめた「集約データ」を返します。
#
# 【TimescaleDB time_bucket概念】
#   TimescaleDBのtime_bucket関数を使って、センサーデータを
#   一定時間ごと（バケット）にグループ化し、平均値・最大値
#   などの統計値を計算します。
#
#   例: bucket_seconds=60（60秒ごとにまとめる）
#     時刻          温度データ
#     10:00:00      25.1°C ─┐
#     10:00:30      25.3°C ─┤→ バケット1: 平均 25.2°C
#     10:01:00      26.0°C ─┐
#     10:01:30      26.2°C ─┤→ バケット2: 平均 26.1°C
#
# リクエストボディ（JSON）:
#   {
#     "robot_id": "ロボットのUUID",
#     "sensor_type": "センサータイプ（例: lidar）",
#     "start_time": "開始時刻",
#     "end_time": "終了時刻",
#     "bucket_seconds": バケットの秒数（例: 60）
#   }
#
# 【なぜ GET ではなく POST メソッド？】
#   クエリ条件が複雑なので、URLパラメータではなく
#   リクエストボディ（JSON）で条件を送信しています。
# =============================================================
@router.post("/data/aggregated")
async def get_aggregated_data(
    body: AggregatedDataQuery,  # リクエストボディ（Pydanticモデルで自動バリデーション）
    current_user: CurrentUser,
    sensor_repo: SensorDataRepo,
):
    # SensorType Enumのバリデーション
    try:
        st = SensorType(body.sensor_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensor type: {body.sensor_type}",
        )

    # リポジトリ経由で集約データを取得
    # 内部でTimescaleDBのtime_bucket関数が使われる想定
    return await sensor_repo.get_aggregated(
        robot_id=body.robot_id,
        sensor_type=st,
        start_time=body.start_time,          # 集約の開始時刻
        end_time=body.end_time,              # 集約の終了時刻
        bucket_seconds=body.bucket_seconds,  # バケットの幅（秒単位）
    )


# =============================================================
# センサータイプ一覧取得エンドポイント
# =============================================================
# GET /sensors/types
#
# 利用可能なセンサータイプの一覧を返します。
# フロントエンドのドロップダウンメニューなどで使います。
#
# 戻り値の例:
#   [
#     {"value": "camera", "name": "CAMERA"},
#     {"value": "lidar", "name": "LIDAR"},
#     {"value": "imu", "name": "IMU"}
#   ]
#
# 【リスト内包表記で一覧を生成】
#   SensorType（Enum）を直接forループで回して、
#   各メンバーのvalue（値）とname（名前）を辞書にしています。
#   st.value → Enumの値（例: "camera"）
#   st.name  → Enumのメンバー名（例: "CAMERA"）
# =============================================================
@router.get("/types")
async def list_sensor_types(current_user: CurrentUser):
    return [{"value": st.value, "name": st.name} for st in SensorType]
