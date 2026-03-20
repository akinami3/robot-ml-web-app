"""
=============================================================================
ドメインエンティティのテスト（test_domain.py）
=============================================================================

【ドメインエンティティとは？】
アプリケーションの核となるビジネスロジック（業務ルール）を表現するオブジェクトです。
例: ユーザー、ロボット、データセット、録画セッション

ドメイン駆動設計（DDD: Domain-Driven Design）の考え方に基づいています:
  - エンティティ: 固有のID を持つオブジェクト（例: ユーザーID）
  - 値オブジェクト: 値そのもので識別されるオブジェクト（例: 設定）

【テストの構成】
テストクラスごとにエンティティを分けて、関連するテストをグループ化しています:
  - TestUser: ユーザーの権限テスト
  - TestRobot: ロボットの状態テスト
  - TestDataset: データセットのエクスポート可否テスト
  - TestRecordingConfig: 録画設定のセンサー有効/無効テスト
  - TestRecordingSession: 録画セッションの開始/停止テスト
=============================================================================
"""

# 【future annotations】型ヒントの新しい書き方を使えるようにする
from __future__ import annotations

# 【uuid4】ランダムな一意の識別子（UUID）を生成する関数
from uuid import uuid4

# 【テスト対象のドメインエンティティをインポート】
from app.domain.entities.dataset import Dataset, DatasetStatus
from app.domain.entities.recording import RecordingConfig, RecordingSession
from app.domain.entities.robot import Robot, RobotState
from app.domain.entities.sensor_data import SensorType
from app.domain.entities.user import User, UserRole


# =============================================================================
# ユーザーエンティティのテスト
# =============================================================================
class TestUser:
    """
    ユーザーの権限（ロール）に関するテスト。

    【ロールベースアクセス制御（RBAC）】
    ユーザーの「役割（ロール）」に基づいてアクセス権限を管理する仕組み:
      ADMIN    : 管理者（すべての操作が可能）
      OPERATOR : オペレーター（ロボット操作可能、ユーザー管理不可）
      VIEWER   : 閲覧者（データの閲覧のみ、操作不可）

    【テストの観点】
    各ロールが「できること」と「できないこと」を両方テストすることで、
    権限の設定が正しいことを保証します。
    """

    def test_admin_can_control_robot(self):
        """
        管理者はロボットを操作できることをテスト。

        【Arrange-Act-Assert パターン】
        テストの基本的な構造:
          Arrange（準備）: テストデータを用意する → User を作成
          Act（実行）    : テスト対象の処理を実行 → can_control_robot() を呼ぶ
          Assert（検証） : 結果が期待通りか検証  → assert で True を確認
        """
        # Arrange: ADMIN ロールのユーザーを作成
        user = User(username="admin", email="a@b.com", role=UserRole.ADMIN)
        # Act & Assert: ロボット操作権限があることを検証
        assert user.can_control_robot()

    def test_operator_can_control_robot(self):
        """オペレーターもロボットを操作できることをテスト。"""
        user = User(username="op", email="o@b.com", role=UserRole.OPERATOR)
        assert user.can_control_robot()

    def test_viewer_cannot_control_robot(self):
        """
        閲覧者はロボットを操作できないことをテスト。

        【否定テスト（Negative Test）】
        「できない」ことを確認するテストも重要です。
        assert not で「False」であることを検証します。
        権限の穴（意図しないアクセス許可）を防ぐために不可欠です。
        """
        user = User(username="view", email="v@b.com", role=UserRole.VIEWER)
        # not をつけて「できないこと」を検証
        assert not user.can_control_robot()

    def test_only_admin_can_manage_users(self):
        """
        ユーザー管理権限は管理者のみが持つことをテスト。

        【1つのテストで正/負の両方を検証】
        admin: can_manage_users() → True（管理できる）
        op:    can_manage_users() → False（管理できない）
        同じテスト内で「できる人」と「できない人」を対比させることで、
        権限の境界線が正しいことを確認します。
        """
        admin = User(username="admin", email="a@b.com", role=UserRole.ADMIN)
        op = User(username="op", email="o@b.com", role=UserRole.OPERATOR)
        assert admin.can_manage_users()
        assert not op.can_manage_users()

    def test_all_roles_can_view(self):
        """
        すべてのロールがデータを閲覧できることをテスト。

        【enum（列挙型）のイテレーション】
        UserRole の全メンバーを for ループで処理:
          for role in UserRole:  → ADMIN, OPERATOR, VIEWER を順番に処理

        【利点】
        新しいロールが追加されても、このテストが自動的にカバーします。
        ロールを手動で列挙すると、追加時にテストの更新を忘れるリスクがある。
        """
        for role in UserRole:
            user = User(username="u", email="u@b.com", role=role)
            # すべてのロールで閲覧権限があることを確認
            assert user.can_view_data()


# =============================================================================
# ロボットエンティティのテスト
# =============================================================================
class TestRobot:
    """
    ロボットの接続状態に関するテスト。

    【ロボットの状態遷移（State Machine）】
      DISCONNECTED → IDLE → MOVING → IDLE → ...
                         ↓
                    EMERGENCY_STOPPED

    各状態の意味:
      DISCONNECTED:      通信が切断されている
      IDLE:              接続済みで待機中
      MOVING:            移動中
      EMERGENCY_STOPPED: 緊急停止中（安全のため即座に停止）
    """

    def test_disconnected_is_not_connected(self):
        """
        切断状態のロボットは「接続されていない」と判定されることをテスト。

        【デフォルト状態のテスト】
        state を指定しない場合、デフォルト値（DISCONNECTED）が使われる。
        デフォルト値が正しく機能するかも重要なテスト観点です。
        """
        robot = Robot(name="test", adapter_type="mock")
        # is_connected は state が DISCONNECTED でないことを確認するプロパティ
        assert not robot.is_connected

    def test_idle_is_connected(self):
        """
        IDLE（待機中）状態のロボットは「接続されている」と判定されることをテスト。
        """
        robot = Robot(name="test", adapter_type="mock", state=RobotState.IDLE)
        assert robot.is_connected

    def test_emergency_stopped(self):
        """
        緊急停止状態のロボットを正しく検出できることをテスト。

        【安全機能のテスト】
        ロボット制御において、緊急停止の検出は最も重要な安全機能の1つです。
        この判定が正しく動作しないと、重大な事故につながる可能性があるため、
        必ずテストで検証します。
        """
        robot = Robot(
            name="test", adapter_type="mock", state=RobotState.EMERGENCY_STOPPED
        )
        assert robot.is_emergency_stopped


# =============================================================================
# データセットエンティティのテスト
# =============================================================================
class TestDataset:
    """
    データセットのエクスポート（書き出し）可否に関するテスト。

    【エクスポートできる条件】
    2つの条件を同時に満たす必要があります:
      1. ステータスが READY（準備完了）であること
      2. レコード数が 1 以上（データが存在する）こと

    【境界値テスト / エッジケーステスト】
    正常ケースだけでなく、境界的な条件もテストします:
      - record_count=0  : ちょうど 0 のとき（空のデータセット）
      - status=CREATING : まだ作成中のとき
    これらの「エッジケース」をテストすることで、バグを早期に発見できます。
    """

    def test_is_exportable_when_ready(self):
        """
        READY状態でデータがある場合、エクスポート可能であることをテスト。

        【正常系テスト（Happy Path）】
        すべての条件が整っている理想的なケースのテストです。
        最も基本的なテストで、まずこれが通ることを確認します。
        """
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.READY,
            record_count=100,
        )
        assert ds.is_exportable

    def test_not_exportable_when_empty(self):
        """
        データが空（record_count=0）の場合、エクスポートできないことをテスト。

        【エッジケース: 空のデータセット】
        ステータスは READY だが、中身が空のケース。
        空のファイルをエクスポートしても意味がないため、ブロックします。
        record_count=0 は境界値（ちょうどデータがない状態）です。
        """
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.READY,
            record_count=0,
        )
        assert not ds.is_exportable

    def test_not_exportable_when_creating(self):
        """
        作成中（CREATING）の場合、エクスポートできないことをテスト。

        【エッジケース: 不完全なデータ】
        レコードはあるが、まだ作成途中のケース。
        不完全なデータをエクスポートするとデータ破損の原因になるため、
        ステータスが READY になるまでエクスポートをブロックします。
        """
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.CREATING,
            record_count=100,
        )
        assert not ds.is_exportable


# =============================================================================
# 録画設定（RecordingConfig）のテスト
# =============================================================================
class TestRecordingConfig:
    """
    センサー録画設定に関するテスト。

    【RecordingConfig の仕組み】
    ロボットのセンサーデータを録画する際に、どのセンサーを有効にするかを設定:
      - sensor_types が空（未指定）: すべてのセンサーを録画
      - sensor_types にセンサーを指定: 指定したセンサーのみ録画
      - enabled=False: 録画自体を無効化
    """

    def test_all_sensors_when_empty(self):
        """
        センサー未指定時はすべてのセンサーが有効であることをテスト。

        【デフォルト動作のテスト】
        sensor_types を指定しない場合、すべてのセンサーが有効になるべきです。
        これは「設定なし ＝ 全部有効」というデフォルト動作の検証です。
        ユーザーが何も設定しなくても正しく動作することを保証します。
        """
        config = RecordingConfig()
        assert config.is_sensor_enabled(SensorType.LIDAR)
        assert config.is_sensor_enabled(SensorType.IMU)

    def test_specific_sensors_only(self):
        """
        特定のセンサーだけを有効にした場合のテスト。

        【包含/除外の検証】
        指定したセンサー（LIDAR, IMU）:  有効（True）
        指定しなかったセンサー（CAMERA）: 無効（False）
        → 「含まれるもの」と「含まれないもの」の両方を必ずテストします
        """
        config = RecordingConfig(sensor_types=[SensorType.LIDAR, SensorType.IMU])
        assert config.is_sensor_enabled(SensorType.LIDAR)     # 指定した → 有効
        assert not config.is_sensor_enabled(SensorType.CAMERA) # 指定なし → 無効

    def test_disabled_config(self):
        """
        録画を無効にした場合、センサーも無効になることをテスト。

        【優先度のテスト】
        enabled=False が sensor_types の設定より優先されることを確認。
        LIDAR は sensor_types に含まれているが、録画自体が無効なので
        is_sensor_enabled は False を返すべきです。
        """
        config = RecordingConfig(
            sensor_types=[SensorType.LIDAR],
            enabled=False,
        )
        # sensor_types に LIDAR があっても enabled=False なら無効
        assert not config.is_sensor_enabled(SensorType.LIDAR)


# =============================================================================
# 録画セッション（RecordingSession）のテスト
# =============================================================================
class TestRecordingSession:
    """
    録画セッションのライフサイクルに関するテスト。

    【録画セッションのライフサイクル】
      開始（作成時）→ 録画中（is_active=True）→ 停止（stop()）→ 終了（is_active=False）
    """

    def test_stop_session(self):
        """
        セッションの開始から停止までの一連の流れをテスト。

        【状態遷移テスト】
        オブジェクトの状態が正しく変化することを検証します:
          1. 作成直後: is_active = True（録画中）
          2. stop()後: is_active = False（停止済み）
          3. stop()後: stopped_at に停止時刻が記録される

        【None チェック】
        stopped_at is not None → 停止時刻が設定されていることを確認
        「None でないこと」の検証は、値の存在確認の基本パターンです。
        """
        # Arrange: 新しい録画セッションを作成
        session = RecordingSession(
            robot_id=uuid4(),     # 録画対象のロボットID
            user_id=uuid4(),      # 録画を開始したユーザーID
            config=RecordingConfig(),  # デフォルトの録画設定
        )

        # Assert: 作成直後はアクティブ（録画中）であること
        assert session.is_active

        # Act: セッションを停止
        session.stop()

        # Assert: 停止後の状態を検証
        assert not session.is_active            # 録画が終了していること
        assert session.stopped_at is not None   # 停止時刻が記録されていること
