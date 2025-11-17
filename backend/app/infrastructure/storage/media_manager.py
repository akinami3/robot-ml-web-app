from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import BinaryIO

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MediaManager:
    def __init__(self, base_path: Path | None = None) -> None:
        settings = get_settings()
        self._base_path = base_path or Path(settings.media_root)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save(self, relative_path: str, file_obj: BinaryIO) -> tuple[Path, str]:
        target_path = self._base_path / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = file_obj.read()
        target_path.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        logger.debug("Saved media asset %s checksum=%s", target_path, checksum)
        return target_path, checksum
