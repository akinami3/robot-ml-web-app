"""Repository protocol definitions for application use cases."""

from __future__ import annotations

import uuid
from typing import Any, Protocol, Sequence

from app.models import DatasetSession, TrainingRun


class DatasetSessionRepositoryProtocol(Protocol):
    async def create(
        self,
        *,
        name: str,
        robot_id: str,
        metadata: dict | None = None,
    ) -> DatasetSession: ...

    async def get(self, session_id: uuid.UUID) -> DatasetSession | None: ...

    async def mark_inactive(self, session_id: uuid.UUID) -> None: ...

    async def get_active_by_robot(self, robot_id: str) -> DatasetSession | None: ...

    async def delete(self, session_id: uuid.UUID) -> None: ...


class SensorDataRepositoryProtocol(Protocol):
    async def add_entry(
        self,
        *,
        session_id: uuid.UUID,
        sensor_type: str,
        payload: dict,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> None: ...

    async def delete_for_session(self, session_id: uuid.UUID) -> None: ...


class RobotStateRepositoryProtocol(Protocol):
    async def create_state(
        self,
        *,
        robot_id: str,
        status: str,
        battery_level: float,
        session_id: uuid.UUID | None = None,
    ) -> Any: ...


class TrainingRunRepositoryProtocol(Protocol):
    async def create_run(
        self,
        *,
        model_name: str,
        dataset_session_id: uuid.UUID | None,
        params: dict[str, Any],
    ) -> TrainingRun: ...

    async def get(self, run_id: uuid.UUID) -> TrainingRun | None: ...


class TrainingMetricRepositoryProtocol(Protocol):
    async def list_for_run(self, run_id: uuid.UUID) -> Sequence[Any]: ...


class RAGDocumentRepositoryProtocol(Protocol):
    async def add_document(self, *, content: str, metadata: dict | None = None) -> Any: ...

    async def list_documents(self, *, robot_id: str | None = None) -> Sequence[dict[str, Any]]: ...