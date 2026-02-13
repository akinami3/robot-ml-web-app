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

from ...domain.entities.sensor_data import SensorData, SensorType
from ...domain.services.recording_service import RecordingService

logger = structlog.get_logger()


class RecordingWorker:
    """Background worker that consumes Redis Streams and records sensor data."""

    def __init__(
        self,
        redis_client: redis.Redis,
        recording_service: RecordingService,
        consumer_group: str = "backend-workers",
        consumer_name: str = "worker-1",
        batch_size: int = 50,
        block_ms: int = 1000,
    ) -> None:
        self._redis = redis_client
        self._recording_service = recording_service
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._batch_size = batch_size
        self._block_ms = block_ms
        self._running = False
        self._task: asyncio.Task | None = None
        self._streams = {
            "robot:sensor_data": ">",
            "robot:commands": ">",
        }

    async def start(self) -> None:
        """Start the recording worker."""
        if self._running:
            return

        # Create consumer groups if they don't exist
        for stream in self._streams:
            try:
                await self._redis.xgroup_create(
                    stream, self._consumer_group, id="0", mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(
            "recording_worker_started",
            consumer_group=self._consumer_group,
            consumer_name=self._consumer_name,
        )

    async def stop(self) -> None:
        """Stop the recording worker."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("recording_worker_stopped")

    async def _run(self) -> None:
        """Main consumer loop."""
        while self._running:
            try:
                results = await self._redis.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=self._consumer_name,
                    streams=self._streams,
                    count=self._batch_size,
                    block=self._block_ms,
                )

                if not results:
                    continue

                for stream_name, messages in results:
                    for msg_id, fields in messages:
                        try:
                            await self._process_message(stream_name, fields)
                            # Acknowledge message
                            await self._redis.xack(
                                stream_name, self._consumer_group, msg_id
                            )
                        except Exception as e:
                            logger.error(
                                "message_processing_error",
                                stream=stream_name,
                                msg_id=msg_id,
                                error=str(e),
                            )

            except asyncio.CancelledError:
                break
            except redis.ConnectionError as e:
                logger.error("redis_connection_error", error=str(e))
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("recording_worker_error", error=str(e))
                await asyncio.sleep(1)

    async def _process_message(
        self, stream_name: str, fields: dict
    ) -> None:
        """Process a single message from Redis Streams."""
        if stream_name == "robot:sensor_data":
            await self._process_sensor_data(fields)
        elif stream_name == "robot:commands":
            await self._process_command(fields)

    async def _process_sensor_data(self, fields: dict) -> None:
        """Process sensor data message and record if active session exists."""
        robot_id_str = fields.get("robot_id", "")
        sensor_type_str = fields.get("sensor_type", "")
        data_str = fields.get("data", "{}")

        if not robot_id_str or not sensor_type_str:
            return

        try:
            robot_id = UUID(robot_id_str)
            sensor_type = SensorType(sensor_type_str)
        except (ValueError, KeyError):
            return

        # Check if recording is active for this robot/sensor
        session = await self._recording_service.should_record(robot_id, sensor_type)
        if session is None:
            return

        # Parse data
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            data = {"raw": data_str}

        # Create sensor data entity
        sensor_data = SensorData(
            robot_id=robot_id,
            sensor_type=sensor_type,
            data=data,
            timestamp=datetime.utcnow(),
        )

        await self._recording_service.record_data(session, sensor_data)

    async def _process_command(self, fields: dict) -> None:
        """Process command message (for audit trail in recording)."""
        # Commands are logged via audit service separately
        # Here we could store them as part of recording if needed
        logger.debug("command_received", fields=fields)
