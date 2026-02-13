"""Dataset domain entity."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


class DatasetStatus(str, enum.Enum):
    CREATING = "creating"
    READY = "ready"
    EXPORTING = "exporting"
    ARCHIVED = "archived"
    ERROR = "error"


class DatasetExportFormat(str, enum.Enum):
    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    ROSBAG = "rosbag"  # future
    HDF5 = "hdf5"


@dataclass
class Dataset:
    name: str
    description: str
    owner_id: UUID
    id: UUID = field(default_factory=uuid4)
    status: DatasetStatus = DatasetStatus.CREATING
    sensor_types: list[str] = field(default_factory=list)
    robot_ids: list[UUID] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    record_count: int = 0
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_exportable(self) -> bool:
        return self.status == DatasetStatus.READY and self.record_count > 0
