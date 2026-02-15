# ============================================================
# 録画サービス（Recording Service）
# ============================================================
# センサーデータの録画（記録）セッションを管理する
# ビジネスロジックを担当するサービスクラスです。
#
# 【録画セッションの流れ】
# 1. ユーザーが録画を開始（start_recording）
#    → ロボットの重複録画チェック
#    → RecordingSession エンティティを作成
# 2. センサーデータが届くたびに記録（record_data）
#    → session_id を付与して保存
#    → 100件ごとに統計情報を更新
# 3. ユーザーが録画を停止（stop_recording）
#    → stopped_at に現在時刻をセット
#    → is_active を False に変更
#
# 【重要な制約】
# 1つのロボットにつき、同時に1つの録画セッションのみ実行可能。
# ============================================================
"""Recording service - domain logic for sensor data recording."""

from __future__ import annotations

import structlog
from uuid import UUID

# 録画設定と録画セッションのエンティティ
from ..entities.recording import RecordingConfig, RecordingSession
# センサーデータとセンサータイプ
from ..entities.sensor_data import SensorData, SensorType
# リポジトリのインターフェース
from ..repositories.recording_repository import RecordingRepository
from ..repositories.sensor_data_repository import SensorDataRepository

logger = structlog.get_logger()


class RecordingService:
    """
    録画セッションに関するビジネスロジックを提供するサービスクラス。

    2つのリポジトリに依存：
    - RecordingRepository: 録画セッションの管理
    - SensorDataRepository: センサーデータの保存
    """

    def __init__(
        self,
        recording_repo: RecordingRepository,
        sensor_data_repo: SensorDataRepository,
    ) -> None:
        """
        コンストラクタ。2つのリポジトリを依存性注入で受け取る。

        Args:
            recording_repo: 録画セッションリポジトリ
            sensor_data_repo: センサーデータリポジトリ
        """
        self._recording_repo = recording_repo
        self._sensor_data_repo = sensor_data_repo

    async def start_recording(
        self,
        robot_id: UUID,
        user_id: UUID,
        config: RecordingConfig,
    ) -> RecordingSession:
        """
        録画セッションを開始する。

        【重複チェック】
        同じロボットで既に録画中のセッションがある場合は ValueError を発生。
        これにより、データの整合性を保つ。

        Args:
            robot_id: 録画対象のロボットID
            user_id: 録画を開始するユーザーID
            config: 録画設定（対象センサータイプ、最大周波数等）
        Returns:
            作成された録画セッション
        Raises:
            ValueError: 既に録画中のセッションがある場合
        """
        # 重複チェック: このロボットで既に録画中でないか確認
        existing = await self._recording_repo.get_active_by_robot(robot_id)
        if existing is not None:
            # ValueError を raise して呼び出し元（エンドポイント）に通知
            raise ValueError(
                f"Already recording for robot {robot_id}, session {existing.id}"
            )

        # 新しい録画セッションを作成
        session = RecordingSession(
            robot_id=robot_id,
            user_id=user_id,
            config=config,
        )
        # データベースに保存
        created = await self._recording_repo.create(session)

        # 構造化ログに記録
        logger.info(
            "recording_started",
            session_id=str(created.id),
            robot_id=str(robot_id),
            # リスト内包表記でセンサータイプを文字列に変換
            sensor_types=[st.value for st in config.sensor_types],
        )
        return created

    async def stop_recording(self, session_id: UUID) -> RecordingSession | None:
        """
        録画セッションを停止する。

        RecordingSession の stop() メソッドを呼び出して、
        is_active を False に、stopped_at に現在時刻を設定する。

        Args:
            session_id: 停止するセッションのID
        Returns:
            停止されたセッション、またはセッションが見つからなければ None
        """
        # セッションをIDで検索
        session = await self._recording_repo.get_by_id(session_id)
        if session is None:
            return None

        # セッションを停止（エンティティの stop() メソッドを呼ぶ）
        session.stop()
        # 更新をデータベースに反映
        updated = await self._recording_repo.update(session)

        logger.info(
            "recording_stopped",
            session_id=str(session_id),
            record_count=session.record_count,
            # duration_seconds: 録画開始から停止までの秒数を計算するプロパティ
            duration=session.duration_seconds,
        )
        return updated

    async def should_record(
        self, robot_id: UUID, sensor_type: SensorType
    ) -> RecordingSession | None:
        """
        このセンサーデータを記録すべきかどうかを判定する。

        【使用タイミング】
        ゲートウェイからセンサーデータが届いた時に呼び出される。
        アクティブなセッションがあり、そのセンサータイプが
        記録対象に含まれている場合のみ、セッションを返す。

        Args:
            robot_id: データを送信したロボットのID
            sensor_type: センサーの種類
        Returns:
            記録すべき場合はアクティブなセッション、不要なら None
        """
        # このロボットのアクティブなセッションを取得
        session = await self._recording_repo.get_active_by_robot(robot_id)
        if session is None:
            return None
        # このセンサータイプが記録対象に含まれているか確認
        if not session.config.is_sensor_enabled(sensor_type):
            return None
        return session

    async def record_data(
        self, session: RecordingSession, data: SensorData
    ) -> None:
        """
        1件のセンサーデータを録画セッションに記録する。

        【バッチ更新の仕組み】
        毎回統計情報を更新するとパフォーマンスが低下するため、
        100件ごとにまとめて統計情報（レコード数・サイズ）を更新する。

        Args:
            session: 記録先の録画セッション
            data: 記録するセンサーデータ
        """
        # センサーデータにセッションIDを紐付け
        data.session_id = session.id
        # データベースに保存
        await self._sensor_data_repo.create(data)

        # レコード数をインクリメント（+1）
        session.record_count += 1

        # 100件ごとに統計情報をデータベースに反映
        # 「% 100 == 0」は「100で割った余りが0」→ 100の倍数のとき
        if session.record_count % 100 == 0:
            await self._recording_repo.update_stats(
                session.id, session.record_count, session.size_bytes
            )

    async def get_session(self, session_id: UUID) -> RecordingSession | None:
        """
        セッションIDで録画セッションを取得する。

        Args:
            session_id: セッションのID
        Returns:
            録画セッション、またはなければ None
        """
        return await self._recording_repo.get_by_id(session_id)

    async def get_user_sessions(self, user_id: UUID) -> list[RecordingSession]:
        """
        ユーザーのアクティブな録画セッション一覧を取得する。

        Args:
            user_id: ユーザーのID
        Returns:
            アクティブな録画セッションのリスト
        """
        return await self._recording_repo.get_active_by_user(user_id)

    async def get_robot_sessions(self, robot_id: UUID) -> list[RecordingSession]:
        """
        ロボットの全録画セッション（過去分含む）を取得する。

        Args:
            robot_id: ロボットのID
        Returns:
            録画セッションのリスト
        """
        return await self._recording_repo.get_by_robot(robot_id)
