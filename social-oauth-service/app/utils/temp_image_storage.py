"""
Temporary Image Storage - handles temporary storage of images for Instagram posting
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
import mimetypes
import imghdr

logger = logging.getLogger(__name__)

# Temporary storage directory
TEMP_IMAGE_DIR = Path("/tmp/social-oauth-temp-images")


class TempImageStorage:
    """Manages temporary storage of images for Instagram posting"""
    
    def __init__(self, temp_dir: Path = TEMP_IMAGE_DIR):
        self.temp_dir = temp_dir
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure temp directory exists"""
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Temp image directory ready: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to create temp directory: {e}")
            raise
    
    def _detect_image_format(self, image_data: bytes) -> Optional[str]:
        """
        Detect actual image format from binary data
        
        Args:
            image_data: Binary image data
        
        Returns:
            Image format (jpeg, png, gif, etc.) or None
        """
        try:
            # Use imghdr to detect format from magic bytes
            format_type = imghdr.what(None, h=image_data)
            return format_type
        except Exception as e:
            logger.warning(f"Failed to detect image format: {e}")
            return None
    
    def _validate_image(self, image_data: bytes) -> bool:
        """
        Validate that binary data is a valid image
        
        Args:
            image_data: Binary image data
        
        Returns:
            True if valid image, False otherwise
        """
        if not image_data or len(image_data) == 0:
            return False
        
        # Detect format
        format_type = self._detect_image_format(image_data)
        
        if format_type not in ['jpeg', 'png', 'gif']:
            logger.warning(f"Invalid or unsupported image format: {format_type}")
            return False
        
        return True
    
    def save_image(self, image_data: bytes, extension: str = "jpg") -> Tuple[str, str]:
        """
        Save binary image data to temporary storage
        
        Args:
            image_data: Binary image data
            extension: File extension (jpg, png, etc.)
        
        Returns:
            Tuple of (filename, full_path)
        """
        try:
            # Validate image data
            if not self._validate_image(image_data):
                raise ValueError("Invalid image data or unsupported format")
            
            # Detect actual format from magic bytes
            detected_format = self._detect_image_format(image_data)
            if detected_format:
                # Use detected format, normalize jpeg/jpg
                extension = 'jpg' if detected_format == 'jpeg' else detected_format
                logger.info(f"Detected image format: {detected_format}")
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{extension.lstrip('.')}"
            filepath = self.temp_dir / filename
            
            # Write image data
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Saved temp image: {filename} ({len(image_data)} bytes)")
            
            return filename, str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save temp image: {e}")
            raise ValueError(f"Failed to save temporary image: {str(e)}")
    
    def get_image_path(self, filename: str) -> Optional[str]:
        """
        Get full path of a temporary image
        
        Args:
            filename: Image filename
        
        Returns:
            Full path if exists, None otherwise
        """
        filepath = self.temp_dir / filename
        if filepath.exists():
            return str(filepath)
        return None
    
    def delete_image(self, filename: str) -> bool:
        """
        Delete a temporary image
        
        Args:
            filename: Image filename
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            filepath = self.temp_dir / filename
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted temp image: {filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete temp image {filename}: {e}")
            return False
    
    def cleanup_old_images(self, max_age_hours: int = 1):
        """
        Clean up images older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            for filepath in self.temp_dir.glob("*"):
                if filepath.is_file():
                    # Check file modification time
                    file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if file_time < cutoff_time:
                        filepath.unlink()
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old temp images")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old images: {e}")
    
    def get_mime_type(self, filename: str) -> str:
        """
        Get MIME type for a filename by detecting from file content
        
        Args:
            filename: Image filename
        
        Returns:
            MIME type string
        """
        filepath = self.get_image_path(filename)
        
        if filepath:
            try:
                # Try to detect format from actual file content
                detected_format = imghdr.what(filepath)
                if detected_format:
                    # Map format to MIME type
                    mime_mapping = {
                        'jpeg': 'image/jpeg',
                        'png': 'image/png',
                        'gif': 'image/gif',
                        'bmp': 'image/bmp',
                        'webp': 'image/webp'
                    }
                    mime_type = mime_mapping.get(detected_format, 'image/jpeg')
                    logger.debug(f"Detected MIME type for {filename}: {mime_type}")
                    return mime_type
            except Exception as e:
                logger.warning(f"Failed to detect MIME type from file content: {e}")
        
        # Fallback to extension-based detection
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'image/jpeg'


# Global instance
temp_image_storage = TempImageStorage()
