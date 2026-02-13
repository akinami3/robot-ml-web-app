"""Recording service - domain logic for sensor data recording."""

from __future__ import annotations

import structlog
from uuid import UUID

from ..entities.recording import RecordingConfig, RecordingSession
from ..entities.sensor_data import SensorData, SensorType
from ..repositories.recording_repository import RecordingRepository
from ..repositories.sensor_data_repository import SensorDataRepository

logger = structlog.get_logger()


class RecordingService:
    def __init__(
        self,
        recording_repo: RecordingRepository,
        sensor_data_repo: SensorDataRepository,
    ) -> None:
        self._recording_repo = recording_repo
        self._sensor_data_repo = sensor_data_repo

    async def start_recording(
        self,
        robot_id: UUID,
        user_id: UUID,
        config: RecordingConfig,
    ) -> RecordingSession:
        # Check if already recording for this robot
        existing = await self._recording_repo.get_active_by_robot(robot_id)
        if existing is not None:
            raise ValueError(
                f"Already recording for robot {robot_id}, session {existing.id}"
            )

        session = RecordingSession(
            robot_id=robot_id,
            user_id=user_id,
            config=config,
        )
        created = await self._recording_repo.create(session)
        logger.info(
            "recording_started",
            session_id=str(created.id),
            robot_id=str(robot_id),
            sensor_types=[st.value for st in config.sensor_types],
        )
        return created

    async def stop_recording(self, session_id: UUID) -> RecordingSession | None:
        session = await self._recording_repo.get_by_id(session_id)
        if session is None:
            return None
        session.stop()
        updated = await self._recording_repo.update(session)
        logger.info(
            "recording_stopped",
            session_id=str(session_id),
            record_count=session.record_count,
            duration=session.duration_seconds,
        )
        return updated

    async def should_record(
        self, robot_id: UUID, sensor_type: SensorType
    ) -> RecordingSession | None:
        """Check if this sensor data should be recorded. Returns the active session if yes."""
        session = await self._recording_repo.get_active_by_robot(robot_id)
        if session is None:
            return None
        if not session.config.is_sensor_enabled(sensor_type):
            return None
        return session

    async def record_data(
        self, session: RecordingSession, data: SensorData
    ) -> None:
        """Record a single sensor data point."""
        data.session_id = session.id
        await self._sensor_data_repo.create(data)
        session.record_count += 1
        if session.record_count % 100 == 0:
            await self._recording_repo.update_stats(
                session.id, session.record_count, session.size_bytes
            )

    async def get_session(self, session_id: UUID) -> RecordingSession | None:
        return await self._recording_repo.get_by_id(session_id)

    async def get_user_sessions(self, user_id: UUID) -> list[RecordingSession]:
        return await self._recording_repo.get_active_by_user(user_id)

    async def get_robot_sessions(self, robot_id: UUID) -> list[RecordingSession]:
        return await self._recording_repo.get_by_robot(robot_id)
