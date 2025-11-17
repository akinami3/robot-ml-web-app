from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(self, scripts_dir: Path | None = None) -> None:
        settings = get_settings()
        self._scripts_dir = scripts_dir or Path("scripts")
        self._start_script = self._scripts_dir / "start_simulation.sh"
        self._stop_script = self._scripts_dir / "stop_simulation.sh"

    def start(self) -> None:
        self._run_script(self._start_script)

    def stop(self) -> None:
        self._run_script(self._stop_script)

    def _run_script(self, script: Path) -> None:
        if not script.exists():
            logger.warning("Simulation script not found: %s", script)
            return
        logger.info("Executing simulation script %s", script)
        subprocess.Popen(["/bin/bash", str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
