"""
Recording service for data collection
"""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.config import settings
from app.core.exceptions import RecordingException
from app.models.dataset import RecordingSession, RobotDataPoint
from app.repositories.dataset import recording_session_repo, robot_data_point_repo
from app.schemas.database import RecordingSessionCreate

logger = get_logger(__name__)


class RecordingService:
    """Service for managing data recording sessions"""

    def __init__(self):
        self.active_sessions: Dict[UUID, bool] = {}  # session_id -> is_recording

    async def start_recording(
        self, db: AsyncSession, session_data: RecordingSessionCreate
    ) -> RecordingSession:
        """
        Start a new recording session
        
        Args:
            db: Database session
            session_data: Recording session configuration
            
        Returns:
            Created recording session
        """
        try:
            # Check if there's already an active session
            active_session = await recording_session_repo.get_active(db)
            if active_session:
                raise RecordingException(
                    f"Active recording session already exists: {active_session.id}"
                )

            # Create recording session
            session_dict = {
                "name": session_data.name,
                "description": session_data.description,
                "selected_data_types": session_data.selected_data_types,
                "status": "recording",
                "start_time": datetime.utcnow(),
            }

            db_session = await recording_session_repo.create(db, obj_in=session_dict)
            self.active_sessions[db_session.id] = True

            logger.info("recording_started", session_id=str(db_session.id))

            return db_session

        except RecordingException:
            raise
        except Exception as e:
            logger.error("recording_start_error", error=str(e))
            raise RecordingException(f"Failed to start recording: {str(e)}")

    async def pause_recording(self, db: AsyncSession, session_id: UUID) -> RecordingSession:
        """Pause recording session"""
        try:
            session = await recording_session_repo.get(db, session_id)
            if not session:
                raise RecordingException(f"Session not found: {session_id}")

            if session.status != "recording":
                raise RecordingException(f"Session is not recording: {session.status}")

            update_data = {
                "status": "paused",
                "pause_time": datetime.utcnow(),
            }

            updated_session = await recording_session_repo.update(
                db, db_obj=session, obj_in=update_data
            )
            self.active_sessions[session_id] = False

            logger.info("recording_paused", session_id=str(session_id))

            return updated_session

        except RecordingException:
            raise
        except Exception as e:
            logger.error("recording_pause_error", error=str(e))
            raise RecordingException(f"Failed to pause recording: {str(e)}")

    async def resume_recording(
        self, db: AsyncSession, session_id: UUID
    ) -> RecordingSession:
        """Resume paused recording session"""
        try:
            session = await recording_session_repo.get(db, session_id)
            if not session:
                raise RecordingException(f"Session not found: {session_id}")

            if session.status != "paused":
                raise RecordingException(f"Session is not paused: {session.status}")

            update_data = {"status": "recording"}

            updated_session = await recording_session_repo.update(
                db, db_obj=session, obj_in=update_data
            )
            self.active_sessions[session_id] = True

            logger.info("recording_resumed", session_id=str(session_id))

            return updated_session

        except RecordingException:
            raise
        except Exception as e:
            logger.error("recording_resume_error", error=str(e))
            raise RecordingException(f"Failed to resume recording: {str(e)}")

    async def save_recording(self, db: AsyncSession, session_id: UUID) -> RecordingSession:
        """Save and complete recording session"""
        try:
            session = await recording_session_repo.get(db, session_id)
            if not session:
                raise RecordingException(f"Session not found: {session_id}")

            update_data = {
                "status": "completed",
                "end_time": datetime.utcnow(),
            }

            updated_session = await recording_session_repo.update(
                db, db_obj=session, obj_in=update_data
            )

            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            logger.info("recording_saved", session_id=str(session_id))

            return updated_session

        except RecordingException:
            raise
        except Exception as e:
            logger.error("recording_save_error", error=str(e))
            raise RecordingException(f"Failed to save recording: {str(e)}")

    async def discard_recording(
        self, db: AsyncSession, session_id: UUID
    ) -> RecordingSession:
        """Discard recording session"""
        try:
            session = await recording_session_repo.get(db, session_id)
            if not session:
                raise RecordingException(f"Session not found: {session_id}")

            update_data = {
                "status": "discarded",
                "end_time": datetime.utcnow(),
            }

            updated_session = await recording_session_repo.update(
                db, db_obj=session, obj_in=update_data
            )

            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            logger.info("recording_discarded", session_id=str(session_id))

            return updated_session

        except RecordingException:
            raise
        except Exception as e:
            logger.error("recording_discard_error", error=str(e))
            raise RecordingException(f"Failed to discard recording: {str(e)}")

    async def add_data_point(
        self, db: AsyncSession, session_id: UUID, data: Dict
    ) -> RobotDataPoint:
        """
        Add data point to recording session
        
        Args:
            db: Database session
            session_id: Recording session ID
            data: Robot data
            
        Returns:
            Created data point
        """
        try:
            # Check if session is actively recording
            if session_id not in self.active_sessions or not self.active_sessions[session_id]:
                return None

            data_point = await robot_data_point_repo.create(db, obj_in=data)
            return data_point

        except Exception as e:
            logger.error("data_point_add_error", error=str(e))
            # Don't raise exception to avoid disrupting recording
            return None


# Singleton instance
_recording_service: Optional[RecordingService] = None


def get_recording_service() -> RecordingService:
    """Get recording service instance"""
    global _recording_service
    if _recording_service is None:
        _recording_service = RecordingService()
    return _recording_service
