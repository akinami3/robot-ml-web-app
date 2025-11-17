from __future__ import annotations

from datetime import datetime
from typing import Iterable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.database.models.media_asset import MediaAssetModel
from app.infrastructure.database.models.telemetry_record import TelemetryRecordModel
from app.infrastructure.database.models.telemetry_session import TelemetrySessionModel, TelemetrySessionStatus


class TelemetryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_session(
        self,
        *,
        device_id: UUID,
        name: str,
        capture_velocity: bool,
        capture_state: bool,
        capture_images: bool,
        session_metadata: dict | None,
    ) -> TelemetrySessionModel:
        session = TelemetrySessionModel(
            device_id=device_id,
            name=name,
            capture_velocity=capture_velocity,
            capture_state=capture_state,
            capture_images=capture_images,
            session_metadata=session_metadata,
            status=TelemetrySessionStatus.PENDING,
        )
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def update_session_status(self, session_id: UUID, status: TelemetrySessionStatus) -> TelemetrySessionModel:
        session = self._db.query(TelemetrySessionModel).filter(TelemetrySessionModel.id == session_id).one()
        session.status = status
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_session(self, session_id: UUID) -> TelemetrySessionModel:
        return self._db.query(TelemetrySessionModel).filter(TelemetrySessionModel.id == session_id).one()

    def list_sessions(self) -> Sequence[TelemetrySessionModel]:
        return (
            self._db.query(TelemetrySessionModel)
            .order_by(TelemetrySessionModel.created_at.desc())
            .all()
        )

    def bulk_insert_records(self, records: Iterable[TelemetryRecordModel]) -> None:
        self._db.add_all(records)
        self._db.commit()

    def create_media_asset(
        self,
        *,
        session_id: UUID,
        record_id: UUID | None,
        asset_type: str,
        file_path: str,
        checksum: str | None,
        mime_type: str | None,
    ) -> MediaAssetModel:
        asset = MediaAssetModel(
            session_id=session_id,
            record_id=record_id,
            asset_type=asset_type,
            file_path=file_path,
            checksum=checksum,
            mime_type=mime_type,
        )
        self._db.add(asset)
        self._db.commit()
        self._db.refresh(asset)
        return asset
