"""
Cloudinary Image Uploader - handles uploading images to Cloudinary
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CloudinaryUploader:
    """Manages image uploads to Cloudinary"""
    
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initialize Cloudinary uploader
        
        Args:
            cloud_name: Cloudinary cloud name
            api_key: Cloudinary API key
            api_secret: Cloudinary API secret
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        logger.info(f"Cloudinary configured for cloud: {cloud_name}")
    
    def upload_image(
        self, 
        image_data: bytes,
        folder: str = "instagram",
        public_id: Optional[str] = None,
        resource_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Upload image to Cloudinary
        
        Args:
            image_data: Binary image data
            folder: Cloudinary folder to upload to
            public_id: Optional public ID for the image
            resource_type: Resource type (default: "image")
        
        Returns:
            Dict containing upload response with image URLs
            
        Raises:
            ValueError: If upload fails
        """
        try:
            logger.info(f"Uploading image to Cloudinary (size: {len(image_data)} bytes)")
            
            # Upload options
            upload_options = {
                'folder': folder,
                'resource_type': resource_type,
                'quality': 'auto',
                'fetch_format': 'auto',
            }
            
            if public_id:
                upload_options['public_id'] = public_id
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                image_data,
                **upload_options
            )
            
            if result and result.get('secure_url'):
                logger.info(f"Image uploaded successfully to Cloudinary: {result['secure_url']}")
                
                return {
                    'success': True,
                    'url': result['secure_url'],  # HTTPS URL
                    'public_url': result.get('url'),  # HTTP URL
                    'public_id': result['public_id'],
                    'asset_id': result.get('asset_id'),
                    'width': result.get('width'),
                    'height': result.get('height'),
                    'format': result.get('format'),
                    'resource_type': result.get('resource_type'),
                    'created_at': result.get('created_at'),
                    'bytes': result.get('bytes'),
                    'version': result.get('version'),
                    'version_id': result.get('version_id'),
                    'signature': result.get('signature'),
                    'etag': result.get('etag')
                }
            else:
                error_msg = "Cloudinary upload failed - no secure_url in response"
                logger.error(f"{error_msg}: {result}")
                raise ValueError(error_msg)
                
        except cloudinary.exceptions.Error as e:
            error_msg = f"Cloudinary API error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error uploading to Cloudinary: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def upload_from_url(
        self, 
        image_url: str,
        folder: str = "instagram",
        public_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload image from URL to Cloudinary
        
        Args:
            image_url: URL of the image to upload
            folder: Cloudinary folder to upload to
            public_id: Optional public ID for the image
        
        Returns:
            Dict containing upload response with image URLs
            
        Raises:
            ValueError: If upload fails
        """
        try:
            logger.info(f"Uploading image from URL to Cloudinary: {image_url}")
            
            # Upload options
            upload_options = {
                'folder': folder,
                'quality': 'auto',
                'fetch_format': 'auto',
            }
            
            if public_id:
                upload_options['public_id'] = public_id
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                image_url,
                **upload_options
            )
            
            if result and result.get('secure_url'):
                logger.info(f"Image uploaded successfully to Cloudinary: {result['secure_url']}")
                
                return {
                    'success': True,
                    'url': result['secure_url'],
                    'public_id': result['public_id'],
                    'asset_id': result.get('asset_id')
                }
            else:
                error_msg = "Cloudinary upload failed - no secure_url in response"
                logger.error(f"{error_msg}: {result}")
                raise ValueError(error_msg)
                
        except cloudinary.exceptions.Error as e:
            error_msg = f"Cloudinary API error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Failed to upload image from URL to Cloudinary: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def delete_image(self, public_id: str) -> bool:
        """
        Delete image from Cloudinary
        
        Args:
            public_id: Public ID of the image to delete
        
        Returns:
            True if successful
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                logger.info(f"Image deleted from Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"Failed to delete image from Cloudinary: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image from Cloudinary: {e}")
            return False


def create_cloudinary_uploader(cloud_name: str, api_key: str, api_secret: str) -> CloudinaryUploader:
    """
    Factory function to create Cloudinary uploader instance
    
    Args:
        cloud_name: Cloudinary cloud name
        api_key: Cloudinary API key
        api_secret: Cloudinary API secret
    
    Returns:
        CloudinaryUploader instance
    """
    if not cloud_name or not api_key or not api_secret:
        raise ValueError("Cloudinary credentials (cloud_name, api_key, api_secret) are required")
    
    return CloudinaryUploader(cloud_name, api_key, api_secret)
