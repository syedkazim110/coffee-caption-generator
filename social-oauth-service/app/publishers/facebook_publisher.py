"""
Facebook Publisher - handles posting to Facebook via Graph API
"""
import requests
from typing import Dict, Any, Optional
import logging
import base64
from io import BytesIO

from app.publishers.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class FacebookPublisher(BasePublisher):
    """Publisher for Facebook using Meta Graph API"""
    
    def __init__(self):
        super().__init__('facebook')
        self.graph_api_url = "https://graph.facebook.com/v18.0"
    
    def publish_post(
        self,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish post to Facebook Page
        
        Args:
            access_token: Facebook Page access token
            caption: Post caption/message
            image_url: URL of image (optional)
            image_data: Binary image data (optional)
            **kwargs: Additional parameters (page_id required)
        
        Returns:
            dict with post_id and url
        """
        page_id = kwargs.get('page_id')
        if not page_id:
            raise ValueError("Facebook publishing requires page_id")
        
        try:
            # Determine if this is a photo or text post
            if image_data or (image_url and self.validate_image_url(image_url)):
                return self._publish_photo_post(
                    access_token, 
                    page_id, 
                    caption, 
                    image_url=image_url,
                    image_data=image_data
                )
            else:
                return self._publish_text_post(access_token, page_id, caption)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to publish Facebook post: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _publish_photo_post(
        self,
        access_token: str,
        page_id: str,
        caption: str,
        image_url: str = None,
        image_data: bytes = None
    ) -> Dict[str, Any]:
        """
        Publish a photo post to Facebook Page
        
        Args:
            access_token: Page access token
            page_id: Facebook Page ID
            caption: Post caption
            image_url: Image URL (optional if image_data provided)
            image_data: Binary image data (optional if image_url provided)
        
        Returns:
            Publishing result
        """
        logger.info(f"Publishing photo post to Facebook Page {page_id}")
        
        # Check if we have binary image data or URL
        if image_data:
            # Upload binary image data using multipart/form-data
            logger.info("Uploading binary image data to Facebook")
            files = {
                'source': ('image.jpg', BytesIO(image_data), 'image/jpeg')
            }
            data = {
                'caption': caption,
                'access_token': access_token
            }
            
            response = requests.post(
                f"{self.graph_api_url}/{page_id}/photos",
                data=data,
                files=files,
                timeout=60
            )
        else:
            # Use URL-based upload
            logger.info(f"Uploading image from URL to Facebook")
            response = requests.post(
                f"{self.graph_api_url}/{page_id}/photos",
                data={
                    'url': image_url,
                    'caption': caption,
                    'access_token': access_token
                },
                timeout=60
            )
        
        response.raise_for_status()
        data = response.json()
        post_id = data['id']
        
        logger.info(f"Facebook photo post published successfully: {post_id}")
        
        # Construct post URL
        post_url = f"https://www.facebook.com/{post_id}"
        
        return {
            'post_id': post_id,
            'url': post_url,
            'platform': 'facebook',
            'caption': caption,
            'image_url': image_url or 'binary_upload',
            'status': 'published'
        }
    
    def _publish_text_post(
        self,
        access_token: str,
        page_id: str,
        caption: str
    ) -> Dict[str, Any]:
        """
        Publish a text-only post to Facebook Page
        
        Args:
            access_token: Page access token
            page_id: Facebook Page ID
            caption: Post message
        
        Returns:
            Publishing result
        """
        logger.info(f"Publishing text post to Facebook Page {page_id}")
        
        response = requests.post(
            f"{self.graph_api_url}/{page_id}/feed",
            data={
                'message': caption,
                'access_token': access_token
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        post_id = data['id']
        
        logger.info(f"Facebook text post published successfully: {post_id}")
        
        # Construct post URL
        post_url = f"https://www.facebook.com/{post_id.replace('_', '/posts/')}"
        
        return {
            'post_id': post_id,
            'url': post_url,
            'platform': 'facebook',
            'caption': caption,
            'status': 'published'
        }
    
    def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete Facebook post
        
        Args:
            access_token: Page access token
            post_id: Facebook post ID
        
        Returns:
            True if successful
        """
        try:
            response = requests.delete(
                f"{self.graph_api_url}/{post_id}",
                params={'access_token': access_token},
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Facebook post {post_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Facebook post: {e}")
            return False
    
    def get_post_status(self, access_token: str, post_id: str) -> Dict[str, Any]:
        """
        Get Facebook post status and metrics
        
        Args:
            access_token: Page access token
            post_id: Facebook post ID
        
        Returns:
            Post metrics and status
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{post_id}",
                params={
                    'fields': 'id,message,created_time,permalink_url,likes.summary(true),comments.summary(true),shares',
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'post_id': data.get('id'),
                'url': data.get('permalink_url'),
                'message': data.get('message'),
                'created_time': data.get('created_time'),
                'likes': data.get('likes', {}).get('summary', {}).get('total_count', 0),
                'comments': data.get('comments', {}).get('summary', {}).get('total_count', 0),
                'shares': data.get('shares', {}).get('count', 0),
                'status': 'published'
            }
        except Exception as e:
            logger.error(f"Failed to get Facebook post status: {e}")
            return {
                'post_id': post_id,
                'status': 'unknown',
                'error': str(e)
            }
    
    def get_page_insights(
        self,
        access_token: str,
        page_id: str,
        metrics: list = None
    ) -> Dict[str, Any]:
        """
        Get Facebook Page insights
        
        Args:
            access_token: Page access token
            page_id: Facebook Page ID
            metrics: List of metrics to retrieve
        
        Returns:
            Page insights data
        """
        if not metrics:
            metrics = [
                'page_impressions',
                'page_engaged_users',
                'page_post_engagements',
                'page_fans'
            ]
        
        try:
            response = requests.get(
                f"{self.graph_api_url}/{page_id}/insights",
                params={
                    'metric': ','.join(metrics),
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            insights = {}
            for item in data.get('data', []):
                insights[item['name']] = item['values'][0]['value']
            
            return insights
        except Exception as e:
            logger.error(f"Failed to get Facebook page insights: {e}")
            return {}
    
    def get_page_info(self, access_token: str, page_id: str) -> Dict[str, Any]:
        """
        Get Facebook Page information
        
        Args:
            access_token: Page access token
            page_id: Facebook Page ID
        
        Returns:
            Page information
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{page_id}",
                params={
                    'fields': 'id,name,username,category,fan_count,link',
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Facebook page info: {e}")
            return {}


# Global Facebook publisher instance
facebook_publisher = FacebookPublisher()
