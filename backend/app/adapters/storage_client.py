"""Object storage adapter (MinIO/S3 compatible)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import BinaryIO

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class StorageClient:
    """Asynchronous wrapper around S3-compatible storage."""

    def __init__(self) -> None:
        self._bucket = settings.object_storage_bucket

    async def upload_image(self, *, object_key: str, data: bytes) -> str:
        # Placeholder implementation; replace with real MinIO/S3 SDK
        await asyncio.sleep(0)  # Yield control to event loop
        logger.info("storage.upload_image", object_key=object_key, bucket=self._bucket)
        return f"s3://{self._bucket}/{object_key}"

    async def download_file(self, *, object_key: str) -> bytes:
        await asyncio.sleep(0)
        logger.info("storage.download_file", object_key=object_key, bucket=self._bucket)
        return b""

    async def upload_fileobj(self, *, object_key: str, fileobj: BinaryIO) -> str:
        data = fileobj.read()
        return await self.upload_image(object_key=object_key, data=data)

    async def save_local_copy(self, *, object_key: str, destination: Path) -> Path:
        await asyncio.sleep(0)
        logger.info("storage.save_local", object_key=object_key, destination=str(destination))
        destination.write_bytes(b"")
        return destination
