from __future__ import annotations

import logging
from asyncio import Lock
from collections import deque
from typing import Deque
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.database.models.media_asset import MediaAssetType
from app.infrastructure.database.models.telemetry_record import TelemetryRecordModel
from app.infrastructure.database.models.telemetry_session import TelemetrySessionStatus
from app.infrastructure.storage.media_manager import MediaManager
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.telemetry import TelemetryRecordIn, TelemetrySession, TelemetrySessionCreate

logger = logging.getLogger(__name__)


class TelemetryService:
    def __init__(self, db: Session, media_manager: MediaManager | None = None) -> None:
        self._db = db
        self._repository = TelemetryRepository(db)
        self._media_manager = media_manager or MediaManager()
        settings = get_settings()
        self._buffer: Deque[TelemetryRecordModel] = deque(maxlen=settings.telemetry_buffer_size)
        self._flush_lock = Lock()

    def create_session(self, payload: TelemetrySessionCreate) -> TelemetrySession:
        session = self._repository.create_session(**payload.dict())
        return TelemetrySession.from_orm(session)

    def list_sessions(self) -> list[TelemetrySession]:
        sessions = self._repository.list_sessions()
        return [TelemetrySession.from_orm(session) for session in sessions]

    def set_status(self, session_id: UUID, status: TelemetrySessionStatus) -> TelemetrySession:
        session = self._repository.update_session_status(session_id, status)
        return TelemetrySession.from_orm(session)

    async def buffer_record(self, payload: TelemetryRecordIn) -> None:
        record = TelemetryRecordModel(
            session_id=payload.session_id,
            timestamp=payload.timestamp,
            linear_velocity_x=payload.linear_velocity_x,
            linear_velocity_y=payload.linear_velocity_y,
            angular_velocity_z=payload.angular_velocity_z,
            state=payload.state,
            notes=payload.notes,
        )
        self._buffer.append(record)
        await self.flush_buffer(force=True)

    async def flush_buffer(self, force: bool = False) -> None:
        async with self._flush_lock:
            if not self._buffer:
                return
            if not force and len(self._buffer) < self._buffer.maxlen:
                return
            records = list(self._buffer)
            self._buffer.clear()
            self._repository.bulk_insert_records(records)
            logger.debug("Flushed %d telemetry records", len(records))

    def save_media(
        self,
        *,
        session_id: UUID,
        record_id: UUID | None,
        filename: str,
        file_obj,
        mime_type: str | None,
    ) -> None:
        path, checksum = self._media_manager.save(filename, file_obj)
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        self._repository.create_media_asset(
            session_id=session_id,
            record_id=record_id,
            asset_type=MediaAssetType.IMAGE.value,
            file_path=str(path),
            checksum=checksum,
            mime_type=mime_type,
        )

    def mark_completed(self, session_id: UUID) -> TelemetrySession:
        return self.set_status(session_id, TelemetrySessionStatus.COMPLETED)

    def mark_discarded(self, session_id: UUID) -> TelemetrySession:
        return self.set_status(session_id, TelemetrySessionStatus.DISCARDED)
