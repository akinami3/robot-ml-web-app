"""Job for exporting datasets."""

from __future__ import annotations

import asyncio
import structlog

logger = structlog.get_logger(__name__)


async def export_dataset(session_id: str) -> None:
    logger.info("jobs.export_dataset.started", session_id=session_id)
    await asyncio.sleep(0)
    logger.info("jobs.export_dataset.finished", session_id=session_id)
