"""
Instagram Publisher - handles posting to Instagram via Graph API
"""
import requests
from typing import Dict, Any, Optional
import logging
import time

from app.publishers.base_publisher import BasePublisher
from app.utils.temp_image_storage import temp_image_storage
from app.utils.cloudinary_uploader import create_cloudinary_uploader
from app.config import settings

logger = logging.getLogger(__name__)


class InstagramPublisher(BasePublisher):
    """Publisher for Instagram using Meta Graph API"""
    
    def __init__(self):
        super().__init__('instagram')
        self.graph_api_url = "https://graph.facebook.com/v18.0"
    
    def _verify_image_accessibility(self, image_url: str) -> Dict[str, Any]:
        """
        Verify that an image URL is accessible and get detailed information
        
        Args:
            image_url: URL to verify
        
        Returns:
            Dict with accessibility info: {
                'accessible': bool,
                'status_code': int,
                'content_type': str,
                'content_length': int,
                'response_time_ms': float,
                'final_url': str (after redirects)
            }
        """
        try:
            logger.info(f"Verifying image accessibility: {image_url}")
            
            import time
            start_time = time.time()
            
            # Make a HEAD request to check if image is accessible
            # Try with different User-Agents to simulate Instagram's crawler
            user_agents = [
                'facebookexternalhit/1.1',  # Instagram/Facebook crawler
                'Mozilla/5.0 (compatible; InstagramBot/1.0)',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ]
            
            last_response = None
            for user_agent in user_agents:
                try:
                    response = requests.head(
                        image_url,
                        timeout=10,
                        headers={
                            'User-Agent': user_agent,
                            'Accept': 'image/*',
                            'ngrok-skip-browser-warning': 'true'
                        },
                        allow_redirects=True
                    )
                    last_response = response
                    
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if not last_response:
                return {
                    'accessible': False,
                    'error': 'No response from server'
                }
            
            response = last_response
            response_time = (time.time() - start_time) * 1000
            
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', 0)
            
            result = {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'content_type': content_type,
                'content_length': int(content_length) if content_length else 0,
                'response_time_ms': response_time,
                'final_url': response.url,
                'redirects': len(response.history)
            }
            
            logger.info(f"Image accessibility check:")
            logger.info(f"  - Status: {result['status_code']}")
            logger.info(f"  - Content-Type: {result['content_type']}")
            logger.info(f"  - Size: {result['content_length']} bytes")
            logger.info(f"  - Response time: {result['response_time_ms']:.2f}ms")
            logger.info(f"  - Redirects: {result['redirects']}")
            logger.info(f"  - Final URL: {result['final_url']}")
            
            # Verify it's an image content type
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not return image content type: {content_type}")
                result['accessible'] = False
                result['error'] = f"Invalid content type: {content_type}"
            
            return result
                
        except Exception as e:
            logger.error(f"Failed to verify image accessibility: {e}")
            return {
                'accessible': False,
                'error': str(e)
            }
    
    def publish_post(
        self,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish post to Instagram
        
        Instagram posting is a 2-step process:
        1. Create media container
        2. Publish the container
        
        Args:
            access_token: Instagram access token
            caption: Post caption with hashtags
            image_url: URL of image (optional if image_data provided)
            image_data: Binary image data (optional if image_url provided)
            **kwargs: Additional parameters (instagram_user_id required)
        
        Returns:
            dict with post_id and url
        """
        # Handle binary image data by uploading to Cloudinary
        cloudinary_upload_result = None
        if image_data and not image_url:
            logger.info("Binary image data provided, uploading to Cloudinary")
            try:
                # Check if Cloudinary credentials are configured
                if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
                    raise ValueError(
                        "Cloudinary credentials not configured. Please add CLOUDINARY_CLOUD_NAME, "
                        "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to your .env file. "
                        "Instagram requires publicly accessible image URLs."
                    )
                
                # Create Cloudinary uploader
                cloudinary_uploader = create_cloudinary_uploader(
                    settings.CLOUDINARY_CLOUD_NAME,
                    settings.CLOUDINARY_API_KEY,
                    settings.CLOUDINARY_API_SECRET
                )
                
                # Upload image to Cloudinary
                cloudinary_upload_result = cloudinary_uploader.upload_image(
                    image_data,
                    folder="instagram"
                )
                
                # Use the secure HTTPS URL from Cloudinary
                # Cloudinary is designed for social media and works reliably with Instagram
                image_url = cloudinary_upload_result['url']
                logger.info(f"Using Cloudinary HTTPS URL: {image_url}")
                logger.info(f"Image uploaded to Cloudinary successfully: {image_url}")
                
            except Exception as e:
                logger.error(f"Failed to upload image to Cloudinary: {e}")
                raise ValueError(f"Failed to upload image to Cloudinary: {str(e)}")
        
        if not image_url:
            raise ValueError("Instagram requires an image_url or image_data")
        
        if not self.validate_image_url(image_url):
            raise ValueError(f"Invalid image URL: {image_url}")
        
        # Verify image accessibility (helps debug issues)
        accessibility_result = self._verify_image_accessibility(image_url)
        if not accessibility_result.get('accessible', False):
            error_info = accessibility_result.get('error', 'Unknown error')
            logger.warning(
                f"Image accessibility verification failed for {image_url}. "
                f"Error: {error_info}. "
                "This may cause Instagram API to fail. "
                "Detailed info: " + str(accessibility_result)
            )
        else:
            # Image is accessible to us, but may not be to Instagram's crawler
            logger.info("✅ Image is accessible from our server, but Instagram's crawler may have different access")
            
            # Log a warning about potential ImgBB-Instagram compatibility issues
            if 'ibb.co' in image_url or 'imgbb.com' in image_url:
                logger.warning(
                    "⚠️ Using ImgBB as image host. If Instagram rejects the image:\n"
                    "  - ImgBB may be blocking Instagram's crawler (facebookexternalhit)\n"
                    "  - Rate limiting may be in effect\n"
                    "  - Consider using an alternative image host known to work with Instagram\n"
                    "  - Instagram-compatible hosts: Cloudinary, AWS S3, Azure Blob Storage"
                )
        
        # Get Instagram Business Account ID
        instagram_user_id = kwargs.get('instagram_user_id')
        if not instagram_user_id:
            instagram_user_id = self._get_instagram_account_id(access_token)
        
        try:
            # Step 1: Create media container
            logger.info(f"Creating Instagram media container for user {instagram_user_id}")
            logger.info(f"Using image URL: {image_url}")
            
            container_response = requests.post(
                f"{self.graph_api_url}/{instagram_user_id}/media",
                params={'access_token': access_token},  # Token as query parameter
                data={
                    'image_url': image_url,
                    'caption': caption
                },
                timeout=60
            )
            
            # Check for errors before raising
            if container_response.status_code != 200:
                error_detail = container_response.text
                logger.error(f"Instagram media container creation failed: {error_detail}")
                
                # Check if it's an accessibility issue
                if 'localhost' in image_url or '127.0.0.1' in image_url:
                    raise ValueError(
                        "Instagram cannot access localhost URLs. Please set SERVER_BASE_URL in your .env "
                        "file to a publicly accessible URL (e.g., using ngrok) or deploy to a public server. "
                        f"Current URL: {image_url}"
                    )
                
                raise ValueError(f"Instagram API error: {error_detail}")
            
            container_response.raise_for_status()
            container_data = container_response.json()
            container_id = container_data['id']
            
            logger.info(f"Media container created: {container_id}")
            
            # Wait for media to be processed (Instagram requirement)
            time.sleep(2)
            
            # Step 2: Publish the container
            logger.info(f"Publishing Instagram media container {container_id}")
            
            publish_response = requests.post(
                f"{self.graph_api_url}/{instagram_user_id}/media_publish",
                params={'access_token': access_token},  # Token as query parameter
                data={
                    'creation_id': container_id
                },
                timeout=60
            )
            publish_response.raise_for_status()
            publish_data = publish_response.json()
            media_id = publish_data['id']
            
            logger.info(f"Instagram post published successfully: {media_id}")
            
            # Get post permalink
            permalink = self._get_post_permalink(access_token, media_id)
            
            return {
                'post_id': media_id,
                'url': permalink,
                'platform': 'instagram',
                'caption': caption,
                'image_url': image_url,
                'status': 'published'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to publish Instagram post: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _get_instagram_account_id(self, access_token: str) -> str:
        """
        Get Instagram Business Account ID from Facebook Graph API
        
        Args:
            access_token: Facebook/Instagram access token
        
        Returns:
            Instagram Business Account ID
        """
        try:
            # Use Facebook Graph API to get Instagram Business Account
            response = requests.get(
                "https://graph.facebook.com/v18.0/me/accounts",
                params={
                    'fields': 'instagram_business_account',
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Find first page with Instagram Business Account
            for page in data.get('data', []):
                if 'instagram_business_account' in page:
                    ig_account_id = page['instagram_business_account']['id']
                    logger.info(f"Found Instagram Business Account ID: {ig_account_id}")
                    return ig_account_id
            
            raise ValueError("No Instagram Business Account found. Please connect an Instagram Business Account to your Facebook Page.")
            
        except Exception as e:
            logger.error(f"Failed to get Instagram account ID: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError("Failed to get Instagram account ID")
    
    def _get_post_permalink(self, access_token: str, media_id: str) -> str:
        """
        Get permalink URL for Instagram post
        
        Args:
            access_token: Instagram access token
            media_id: Instagram media ID
        
        Returns:
            Permalink URL
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{media_id}",
                params={
                    'fields': 'permalink',
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('permalink', f'https://www.instagram.com/p/{media_id}/')
        except Exception as e:
            logger.warning(f"Failed to get permalink: {e}")
            return f'https://www.instagram.com/p/{media_id}/'
    
    def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete Instagram post
        
        Args:
            access_token: Instagram access token
            post_id: Instagram media ID
        
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
            logger.info(f"Instagram post {post_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Instagram post: {e}")
            return False
    
    def get_post_status(self, access_token: str, post_id: str) -> Dict[str, Any]:
        """
        Get Instagram post status and metrics
        
        Args:
            access_token: Instagram access token
            post_id: Instagram media ID
        
        Returns:
            Post metrics and status
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{post_id}",
                params={
                    'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                    'access_token': access_token
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'post_id': data.get('id'),
                'url': data.get('permalink'),
                'caption': data.get('caption'),
                'media_type': data.get('media_type'),
                'likes': data.get('like_count', 0),
                'comments': data.get('comments_count', 0),
                'timestamp': data.get('timestamp'),
                'status': 'published'
            }
        except Exception as e:
            logger.error(f"Failed to get Instagram post status: {e}")
            return {
                'post_id': post_id,
                'status': 'unknown',
                'error': str(e)
            }
    
    def get_insights(self, access_token: str, media_id: str) -> Dict[str, Any]:
        """
        Get Instagram post insights/analytics
        
        Args:
            access_token: Instagram access token
            media_id: Instagram media ID
        
        Returns:
            Post insights data
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{media_id}/insights",
                params={
                    'metric': 'engagement,impressions,reach,saved',
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
            logger.error(f"Failed to get Instagram insights: {e}")
            return {}
    
    def _get_server_base_url(self) -> str:
        """
        Get the server base URL for temp image serving
        
        Returns:
            Server base URL
        """
        # Try to get from settings, fallback to localhost
        try:
            base_url = settings.SERVER_BASE_URL
            if base_url:
                return base_url.rstrip('/')
        except AttributeError:
            pass
        
        # Default to localhost with port from settings
        try:
            port = settings.PORT or 8000
            return f"http://localhost:{port}"
        except AttributeError:
            return "http://localhost:8000"


# Global Instagram publisher instance
instagram_publisher = InstagramPublisher()
