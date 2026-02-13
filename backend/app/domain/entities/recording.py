"""Recording session domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from .sensor_data import SensorType


@dataclass
class RecordingConfig:
    """User-configurable recording settings per sensor type."""

    sensor_types: list[SensorType] = field(default_factory=list)
    max_frequency_hz: dict[SensorType, float] = field(default_factory=dict)
    enabled: bool = True

    def is_sensor_enabled(self, sensor_type: SensorType) -> bool:
        if not self.enabled:
            return False
        if not self.sensor_types:
            return True  # empty = all
        return sensor_type in self.sensor_types

    def get_max_frequency(self, sensor_type: SensorType) -> float | None:
        return self.max_frequency_hz.get(sensor_type)


@dataclass
class RecordingSession:
    robot_id: UUID
    user_id: UUID
    config: RecordingConfig
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    record_count: int = 0
    size_bytes: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    stopped_at: datetime | None = None
    dataset_id: UUID | None = None

    def stop(self) -> None:
        self.is_active = False
        self.stopped_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> float | None:
        if self.stopped_at is None:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return (self.stopped_at - self.started_at).total_seconds()
