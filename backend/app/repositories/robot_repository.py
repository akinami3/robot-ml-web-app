from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.infrastructure.database.models.robot_device import RobotDeviceModel


class RobotRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_devices(self) -> Sequence[RobotDeviceModel]:
        return self._db.query(RobotDeviceModel).order_by(RobotDeviceModel.created_at.desc()).all()
