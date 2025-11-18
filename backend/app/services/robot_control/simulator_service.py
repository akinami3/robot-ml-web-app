"""
Simulator management service
"""
import asyncio
import os
import subprocess
from datetime import datetime
from typing import Optional

from structlog import get_logger

from app.config import settings
from app.core.exceptions import SimulatorException

logger = get_logger(__name__)


class SimulatorService:
    """Unity simulator management service"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None

    def is_running(self) -> bool:
        """Check if simulator is running"""
        return self.process is not None and self.process.poll() is None

    async def start(self) -> dict:
        """
        Start Unity simulator
        
        Returns:
            Status dictionary with process info
        """
        if self.is_running():
            logger.warning("simulator_already_running")
            return {
                "is_running": True,
                "process_id": self.process.pid,
                "started_at": self.started_at,
            }

        try:
            # Check if executable exists
            if not os.path.exists(settings.UNITY_EXECUTABLE_PATH):
                raise SimulatorException(
                    f"Simulator executable not found: {settings.UNITY_EXECUTABLE_PATH}"
                )

            # Start simulator process
            self.process = subprocess.Popen(
                [settings.UNITY_EXECUTABLE_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.started_at = datetime.utcnow()

            logger.info(
                "simulator_started",
                pid=self.process.pid,
                executable=settings.UNITY_EXECUTABLE_PATH,
            )

            return {
                "is_running": True,
                "process_id": self.process.pid,
                "started_at": self.started_at,
            }

        except Exception as e:
            logger.error("simulator_start_error", error=str(e))
            raise SimulatorException(f"Failed to start simulator: {str(e)}")

    async def stop(self) -> dict:
        """
        Stop Unity simulator
        
        Returns:
            Status dictionary
        """
        if not self.is_running():
            logger.warning("simulator_not_running")
            return {"is_running": False, "message": "Simulator is not running"}

        try:
            # Terminate process
            self.process.terminate()

            # Wait for process to terminate (with timeout)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("simulator_force_kill")
                self.process.kill()
                self.process.wait()

            pid = self.process.pid
            self.process = None
            self.started_at = None

            logger.info("simulator_stopped", pid=pid)

            return {"is_running": False, "message": "Simulator stopped successfully"}

        except Exception as e:
            logger.error("simulator_stop_error", error=str(e))
            raise SimulatorException(f"Failed to stop simulator: {str(e)}")

    def get_status(self) -> dict:
        """Get simulator status"""
        return {
            "is_running": self.is_running(),
            "process_id": self.process.pid if self.process else None,
            "started_at": self.started_at,
        }


# Singleton instance
_simulator_service: Optional[SimulatorService] = None


def get_simulator_service() -> SimulatorService:
    """Get simulator service instance"""
    global _simulator_service
    if _simulator_service is None:
        _simulator_service = SimulatorService()
    return _simulator_service
