"""
Image storage service
"""
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from structlog import get_logger

from app.config import settings
from app.core.exceptions import RecordingException

logger = get_logger(__name__)


class ImageStorageService:
    """Service for storing robot camera images"""

    def __init__(self):
        self.storage_path = Path(settings.IMAGE_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_image(
        self, image_data: str, session_id: str, timestamp: Optional[datetime] = None
    ) -> str:
        """
        Save image to file system
        
        Args:
            image_data: Base64 encoded image data
            session_id: Recording session ID
            timestamp: Image timestamp
            
        Returns:
            Relative path to saved image
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            # Create session directory
            session_dir = self.storage_path / session_id
            session_dir.mkdir(exist_ok=True)

            # Generate filename with timestamp and hash
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            file_path = session_dir / filename

            # Decode base64 image
            if "," in image_data:
                # Remove data URL prefix if present
                image_data = image_data.split(",", 1)[1]

            image_bytes = base64.b64decode(image_data)

            # Save image asynchronously
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(image_bytes)

            # Return relative path
            relative_path = str(file_path.relative_to(self.storage_path))

            logger.debug("image_saved", path=relative_path, size=len(image_bytes))

            return relative_path

        except Exception as e:
            logger.error("image_save_error", error=str(e))
            raise RecordingException(f"Failed to save image: {str(e)}")

    async def get_image_path(self, relative_path: str) -> Path:
        """Get absolute path for relative image path"""
        return self.storage_path / relative_path

    async def delete_session_images(self, session_id: str) -> None:
        """Delete all images for a session"""
        try:
            session_dir = self.storage_path / session_id
            if session_dir.exists():
                import shutil

                shutil.rmtree(session_dir)
                logger.info("session_images_deleted", session_id=session_id)
        except Exception as e:
            logger.error("image_delete_error", error=str(e))


# Singleton instance
_image_storage_service: Optional[ImageStorageService] = None


def get_image_storage_service() -> ImageStorageService:
    """Get image storage service instance"""
    global _image_storage_service
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    return _image_storage_service
