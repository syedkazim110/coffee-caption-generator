"""
Base Publisher - abstract class for platform-specific publishing
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class BasePublisher(ABC):
    """Base class for social media publishers"""
    
    def __init__(self, platform: str):
        self.platform = platform
    
    @abstractmethod
    def publish_post(
        self,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish a post to the platform
        
        Args:
            access_token: OAuth access token
            caption: Post caption/text
            image_url: URL of image to post (optional)
            **kwargs: Platform-specific parameters
        
        Returns:
            dict with post_id, url, and other platform-specific data
        """
        pass
    
    @abstractmethod
    def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete a post from the platform
        
        Args:
            access_token: OAuth access token
            post_id: Platform post ID
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_post_status(self, access_token: str, post_id: str) -> Dict[str, Any]:
        """
        Get post status and metrics
        
        Args:
            access_token: OAuth access token
            post_id: Platform post ID
        
        Returns:
            dict with post status and metrics
        """
        pass
    
    def format_caption(self, caption: str, hashtags: list = None) -> str:
        """
        Format caption with hashtags
        
        Args:
            caption: Base caption text
            hashtags: List of hashtags
        
        Returns:
            Formatted caption with hashtags
        """
        if not hashtags:
            return caption
        
        # Remove # prefix if present
        clean_hashtags = [tag.lstrip('#') for tag in hashtags]
        hashtag_str = ' '.join([f'#{tag}' for tag in clean_hashtags])
        
        return f"{caption}\n\n{hashtag_str}"
    
    def validate_image_url(self, image_url: str) -> bool:
        """
        Validate image URL
        
        Args:
            image_url: URL to validate
        
        Returns:
            True if valid
        """
        if not image_url:
            return False
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        return any(image_url.lower().endswith(ext) for ext in valid_extensions)
    
    def record_publish_result(
        self,
        brand_id: int,
        scheduled_post_id: Optional[int],
        result: Dict[str, Any],
        success: bool
    ):
        """
        Record publishing result to database
        
        Args:
            brand_id: Brand ID
            scheduled_post_id: Scheduled post ID (if applicable)
            result: Publishing result data
            success: Whether publishing was successful
        """
        from app.database import db
        
        try:
            db.execute_insert(
                """
                INSERT INTO post_history (
                    scheduled_post_id, brand_id, platform,
                    platform_post_id, post_url, caption,
                    status, error_message, published_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    scheduled_post_id,
                    brand_id,
                    self.platform,
                    result.get('post_id'),
                    result.get('url'),
                    result.get('caption'),
                    'success' if success else 'failed',
                    result.get('error'),
                    datetime.now()
                ),
                returning=False
            )
        except Exception as e:
            logger.error(f"Failed to record publish result: {e}")
    
    @retry_with_backoff(max_retries=3, backoff_seconds=5)
    def publish_with_retry(
        self,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish post with automatic retry on failure
        
        Args:
            access_token: OAuth access token
            caption: Post caption
            image_url: Image URL (optional)
            **kwargs: Platform-specific parameters
        
        Returns:
            Publishing result
        """
        return self.publish_post(access_token, caption, image_url, **kwargs)
