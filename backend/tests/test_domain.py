"""Domain entity tests."""

from __future__ import annotations

from uuid import uuid4

from app.domain.entities.dataset import Dataset, DatasetStatus
from app.domain.entities.recording import RecordingConfig, RecordingSession
from app.domain.entities.robot import Robot, RobotState
from app.domain.entities.sensor_data import SensorType
from app.domain.entities.user import User, UserRole


class TestUser:
    def test_admin_can_control_robot(self):
        user = User(username="admin", email="a@b.com", role=UserRole.ADMIN)
        assert user.can_control_robot()

    def test_operator_can_control_robot(self):
        user = User(username="op", email="o@b.com", role=UserRole.OPERATOR)
        assert user.can_control_robot()

    def test_viewer_cannot_control_robot(self):
        user = User(username="view", email="v@b.com", role=UserRole.VIEWER)
        assert not user.can_control_robot()

    def test_only_admin_can_manage_users(self):
        admin = User(username="admin", email="a@b.com", role=UserRole.ADMIN)
        op = User(username="op", email="o@b.com", role=UserRole.OPERATOR)
        assert admin.can_manage_users()
        assert not op.can_manage_users()

    def test_all_roles_can_view(self):
        for role in UserRole:
            user = User(username="u", email="u@b.com", role=role)
            assert user.can_view_data()


class TestRobot:
    def test_disconnected_is_not_connected(self):
        robot = Robot(name="test", adapter_type="mock")
        assert not robot.is_connected

    def test_idle_is_connected(self):
        robot = Robot(name="test", adapter_type="mock", state=RobotState.IDLE)
        assert robot.is_connected

    def test_emergency_stopped(self):
        robot = Robot(
            name="test", adapter_type="mock", state=RobotState.EMERGENCY_STOPPED
        )
        assert robot.is_emergency_stopped


class TestDataset:
    def test_is_exportable_when_ready(self):
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.READY,
            record_count=100,
        )
        assert ds.is_exportable

    def test_not_exportable_when_empty(self):
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.READY,
            record_count=0,
        )
        assert not ds.is_exportable

    def test_not_exportable_when_creating(self):
        ds = Dataset(
            name="test",
            description="desc",
            owner_id=uuid4(),
            status=DatasetStatus.CREATING,
            record_count=100,
        )
        assert not ds.is_exportable


class TestRecordingConfig:
    def test_all_sensors_when_empty(self):
        config = RecordingConfig()
        assert config.is_sensor_enabled(SensorType.LIDAR)
        assert config.is_sensor_enabled(SensorType.IMU)

    def test_specific_sensors_only(self):
        config = RecordingConfig(sensor_types=[SensorType.LIDAR, SensorType.IMU])
        assert config.is_sensor_enabled(SensorType.LIDAR)
        assert not config.is_sensor_enabled(SensorType.CAMERA)

    def test_disabled_config(self):
        config = RecordingConfig(
            sensor_types=[SensorType.LIDAR],
            enabled=False,
        )
        assert not config.is_sensor_enabled(SensorType.LIDAR)


class TestRecordingSession:
    def test_stop_session(self):
        session = RecordingSession(
            robot_id=uuid4(),
            user_id=uuid4(),
            config=RecordingConfig(),
        )
        assert session.is_active
        session.stop()
        assert not session.is_active
        assert session.stopped_at is not None
