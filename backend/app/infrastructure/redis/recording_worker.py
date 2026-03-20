# ============================================================
# Redis Streams 録画ワーカー（Recording Worker）
# ============================================================
# Redis Streams からセンサーデータを受信し、
# アクティブな録画セッションに基づいてデータを保存する
# バックグラウンドワーカーです。
#
# 【Redis Streams とは？】
# メッセージキュー（メッセージを順番に処理する仕組み）の一種。
# プロデューサー（送信者）とコンシューマー（受信者）を分離し、
# データの欠損なく確実にメッセージを届けます。
#
# 【コンシューマーグループとは？】
# 複数のワーカーでメッセージを分散処理する仕組み。
# 同じメッセージが複数のワーカーに配信されることがない。
# ワーカーが処理完了を報告（ACK）するまで、
# メッセージは保持される（再試行可能）。
#
# 【処理の流れ】
# 1. Gateway が Redis Stream にセンサーデータを書き込む
# 2. このワーカーが Stream からデータを読み取る
# 3. 対象ロボットで録画セッションが有効か確認
# 4. 有効なら PostgreSQL にデータを保存
#
# ┌─────────┐    ┌───────────────┐    ┌────────────────┐    ┌──────────┐
# │ Gateway │─→ │ Redis Stream  │─→ │ RecordingWorker│─→ │ PostgreSQL│
# │ (Go)    │    │ (キュー)      │    │ (Python)      │    │ (DB)     │
# └─────────┘    └───────────────┘    └────────────────┘    └──────────┘
# ============================================================
"""Redis Streams recording worker.

Subscribes to robot:sensor_data and robot:commands streams from the Gateway.
Filters data according to active recording sessions and persists to PostgreSQL.
"""

from __future__ import annotations

import asyncio
import json
import structlog
from datetime import datetime
from uuid import UUID, uuid4

import redis.asyncio as redis

# ドメイン層のエンティティとサービス
from ...domain.entities.sensor_data import SensorData, SensorType
from ...domain.services.recording_service import RecordingService

logger = structlog.get_logger()


class RecordingWorker:
    """
    バックグラウンドワーカー: Redis Streams を消費してセンサーデータを記録。

    【バックグラウンドワーカーとは？】
    アプリケーションのメイン処理とは別に、バックグラウンドで
    継続的に動作するプロセス。asyncio.Task として実行される。
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        recording_service: RecordingService,
        consumer_group: str = "backend-workers",
        consumer_name: str = "worker-1",
        batch_size: int = 50,
        block_ms: int = 1000,
    ) -> None:
        """
        コンストラクタ。

        Args:
            redis_client: Redis クライアント
            recording_service: 録画サービス（録画判定とデータ保存を行う）
            consumer_group: コンシューマーグループ名
                → 同じグループのワーカーでメッセージを分散処理
            consumer_name: このワーカーの名前（グループ内で一意）
            batch_size: 1回の読み取りで取得するメッセージ数
            block_ms: 新しいメッセージを待つ最大時間（ミリ秒）
                → 1000ms = 1秒待ってもメッセージがなければ次のループへ
        """
        self._redis = redis_client
        self._recording_service = recording_service
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._batch_size = batch_size
        self._block_ms = block_ms
        self._running = False           # ワーカーの実行状態フラグ
        self._task: asyncio.Task | None = None  # 非同期タスクの参照

        # 監視する Redis Stream のキー
        # ">": 「まだ配信されていない新しいメッセージだけ読む」という意味
        self._streams = {
            "robot:sensor_data": ">",  # センサーデータ用ストリーム
            "robot:commands": ">",     # コマンド用ストリーム
        }

    async def start(self) -> None:
        """
        録画ワーカーを開始する。

        【初期化処理】
        1. 各ストリームにコンシューマーグループを作成
        2. バックグラウンドタスクとしてメインループを起動
        """
        if self._running:
            return  # 既に実行中なら何もしない

        # 各ストリームにコンシューマーグループを作成
        for stream in self._streams:
            try:
                # xgroup_create: コンシューマーグループを作成
                # id="0": ストリームの最初からメッセージを読む
                # mkstream=True: ストリームが存在しなければ自動作成
                await self._redis.xgroup_create(
                    stream, self._consumer_group, id="0", mkstream=True
                )
            except redis.ResponseError as e:
                # "BUSYGROUP": グループが既に存在する場合のエラー → 無視
                if "BUSYGROUP" not in str(e):
                    raise

        self._running = True
        # asyncio.create_task: 非同期関数をバックグラウンドタスクとして起動
        # → メインスレッドをブロックせずに並行実行される
        self._task = asyncio.create_task(self._run())
        logger.info(
            "recording_worker_started",
            consumer_group=self._consumer_group,
            consumer_name=self._consumer_name,
        )

    async def stop(self) -> None:
        """
        録画ワーカーを停止する。

        実行中のタスクをキャンセルして、安全に終了する。
        """
        self._running = False
        if self._task is not None:
            self._task.cancel()  # タスクにキャンセル信号を送る
            try:
                await self._task  # タスクの終了を待つ
            except asyncio.CancelledError:
                pass  # キャンセルは正常な終了なので無視
        logger.info("recording_worker_stopped")

    async def _run(self) -> None:
        """
        メインループ: Redis Stream からメッセージを継続的に読み取る。

        【ループの流れ】
        1. xreadgroup でメッセージをバッチ読み取り
        2. 各メッセージを処理
        3. 処理完了したメッセージを ACK（確認応答）
        4. 1に戻る

        【エラーハンドリング】
        - CancelledError: 正常停止（stop() から）→ ループを抜ける
        - ConnectionError: Redis 切断 → 5秒待って再試行
        - その他のエラー: 1秒待って再試行
        """
        while self._running:
            try:
                # xreadgroup: コンシューマーグループとしてメッセージを読み取る
                # count: 1回に読むメッセージ数
                # block: メッセージがない場合の待ち時間（ミリ秒）
                results = await self._redis.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=self._consumer_name,
                    streams=self._streams,
                    count=self._batch_size,
                    block=self._block_ms,
                )

                # メッセージがなければ次のループへ
                if not results:
                    continue

                # results の構造: [(stream_name, [(msg_id, fields), ...]), ...]
                for stream_name, messages in results:
                    for msg_id, fields in messages:
                        try:
                            # メッセージを処理
                            await self._process_message(stream_name, fields)
                            # xack: メッセージの処理完了を Redis に通知
                            # ACK しないとメッセージは「保留」状態のまま残る
                            await self._redis.xack(
                                stream_name, self._consumer_group, msg_id
                            )
                        except Exception as e:
                            # 個別メッセージのエラーはログに記録して続行
                            logger.error(
                                "message_processing_error",
                                stream=stream_name,
                                msg_id=msg_id,
                                error=str(e),
                            )

            except asyncio.CancelledError:
                break  # 正常停止
            except redis.ConnectionError as e:
                # Redis 接続エラー → 5秒待って再接続を試みる
                logger.error("redis_connection_error", error=str(e))
                await asyncio.sleep(5)
            except Exception as e:
                # その他のエラー → 1秒待って再試行
                logger.error("recording_worker_error", error=str(e))
                await asyncio.sleep(1)

    async def _process_message(
        self, stream_name: str, fields: dict
    ) -> None:
        """
        1つのメッセージを処理する（ストリーム名に応じて振り分け）。

        Args:
            stream_name: メッセージの送信元ストリーム名
            fields: メッセージの内容（キー=値の辞書）
        """
        if stream_name == "robot:sensor_data":
            await self._process_sensor_data(fields)
        elif stream_name == "robot:commands":
            await self._process_command(fields)

    async def _process_sensor_data(self, fields: dict) -> None:
        """
        センサーデータメッセージを処理する。

        【処理の流れ】
        1. メッセージからロボットID、センサータイプ、データを取り出す
        2. 値のバリデーション（検証）
        3. 録画セッションが有効か確認（should_record）
        4. 有効なら SensorData エンティティを作成して保存

        Args:
            fields: Redis Stream メッセージの内容
                例: {"robot_id": "uuid...", "sensor_type": "lidar", "data": "{...}"}
        """
        # メッセージからフィールドを取り出し（存在しなければ空文字列）
        robot_id_str = fields.get("robot_id", "")
        sensor_type_str = fields.get("sensor_type", "")
        data_str = fields.get("data", "{}")

        # 必須フィールドが空なら処理をスキップ
        if not robot_id_str or not sensor_type_str:
            return

        try:
            # 文字列を適切な型に変換
            robot_id = UUID(robot_id_str)           # 文字列 → UUID
            sensor_type = SensorType(sensor_type_str)  # 文字列 → Enum
        except (ValueError, KeyError):
            return  # 無効な値の場合はスキップ

        # このロボット・センサータイプの録画セッションが有効か確認
        session = await self._recording_service.should_record(robot_id, sensor_type)
        if session is None:
            return  # 録画セッションがなければスキップ

        # JSON 文字列をパース（辞書に変換）
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            data = {"raw": data_str}  # パース失敗時はそのまま保存

        # SensorData エンティティを作成
        sensor_data = SensorData(
            robot_id=robot_id,
            sensor_type=sensor_type,
            data=data,
            timestamp=datetime.utcnow(),  # 現在時刻（UTC）
        )

        # 録画サービスを通じてデータを保存
        await self._recording_service.record_data(session, sensor_data)

    async def _process_command(self, fields: dict) -> None:
        """
        コマンドメッセージを処理する。

        現在はデバッグログを出力するだけ。
        将来的にはコマンドも録画データとして保存できるようにする予定。

        Args:
            fields: Redis Stream メッセージの内容
        """
        # コマンドは監査サービスで別途記録されるため、ここではログのみ
        logger.debug("command_received", fields=fields)
