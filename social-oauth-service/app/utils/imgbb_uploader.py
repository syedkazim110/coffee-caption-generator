"""
ImgBB Image Uploader - handles uploading images to imgbb.com
"""
import requests
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ImgBBUploader:
    """Manages image uploads to ImgBB"""
    
    def __init__(self, api_key: str):
        """
        Initialize ImgBB uploader
        
        Args:
            api_key: ImgBB API key
        """
        self.api_key = api_key
        self.upload_url = "https://api.imgbb.com/1/upload"
    
    def upload_image(
        self, 
        image_data: bytes,
        name: Optional[str] = None,
        expiration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Upload image to ImgBB
        
        Args:
            image_data: Binary image data
            name: Optional name for the image
            expiration: Optional expiration time in seconds (60-15552000)
        
        Returns:
            Dict containing upload response with image URLs
            
        Raises:
            ValueError: If upload fails
        """
        try:
            # Encode image data to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare payload
            payload = {
                'key': self.api_key,
                'image': image_base64
            }
            
            if name:
                payload['name'] = name
            
            if expiration:
                payload['expiration'] = expiration
            
            # Upload to ImgBB
            logger.info(f"Uploading image to ImgBB (size: {len(image_data)} bytes)")
            
            response = requests.post(
                self.upload_url,
                data=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                logger.info(f"Image uploaded successfully to ImgBB: {data['url']}")
                
                return {
                    'success': True,
                    'url': data['url'],
                    'display_url': data['display_url'],
                    'delete_url': data.get('delete_url'),
                    'id': data['id'],
                    'title': data.get('title'),
                    'size': data.get('size'),
                    'expiration': data.get('expiration'),
                    'image': {
                        'url': data['image']['url'],
                        'width': data['image'].get('width'),
                        'height': data['image'].get('height')
                    }
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"ImgBB upload failed: {error_msg}")
                raise ValueError(f"ImgBB upload failed: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to upload image to ImgBB: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error uploading to ImgBB: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def upload_from_url(self, image_url: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload image from URL to ImgBB
        
        Args:
            image_url: URL of the image to upload
            name: Optional name for the image
        
        Returns:
            Dict containing upload response with image URLs
            
        Raises:
            ValueError: If upload fails
        """
        try:
            # Prepare payload
            payload = {
                'key': self.api_key,
                'image': image_url
            }
            
            if name:
                payload['name'] = name
            
            # Upload to ImgBB
            logger.info(f"Uploading image from URL to ImgBB: {image_url}")
            
            response = requests.post(
                self.upload_url,
                data=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                data = result['data']
                logger.info(f"Image uploaded successfully to ImgBB: {data['url']}")
                
                return {
                    'success': True,
                    'url': data['url'],
                    'display_url': data['display_url'],
                    'delete_url': data.get('delete_url'),
                    'id': data['id']
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"ImgBB upload failed: {error_msg}")
                raise ValueError(f"ImgBB upload failed: {error_msg}")
                
        except Exception as e:
            error_msg = f"Failed to upload image from URL to ImgBB: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)


def create_imgbb_uploader(api_key: str) -> ImgBBUploader:
    """
    Factory function to create ImgBB uploader instance
    
    Args:
        api_key: ImgBB API key
    
    Returns:
        ImgBBUploader instance
    """
    if not api_key:
        raise ValueError("ImgBB API key is required")
    
    return ImgBBUploader(api_key)
