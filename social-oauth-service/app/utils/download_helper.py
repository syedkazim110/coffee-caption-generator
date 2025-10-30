"""
Download Helper - Similar to Node.js request download utility
Downloads images from URLs to use with media upload
"""
import requests
import logging
from typing import Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


def download(uri: str, filename: str, callback: Optional[Callable] = None) -> bytes:
    """
    Download a file from a URI and save it to disk
    Similar to the Node.js request download pattern
    
    Args:
        uri: URL to download from
        filename: Local filename to save to
        callback: Optional callback function to execute after download
    
    Returns:
        Downloaded image data as bytes
    
    Example:
        download("https://i.imgur.com/example.jpg", "image.png", lambda: print("Done!"))
    """
    try:
        logger.info(f"Downloading from {uri}...")
        
        # Download the file
        response = requests.get(uri, timeout=30, stream=True)
        response.raise_for_status()
        
        image_data = response.content
        logger.info(f"Downloaded {len(image_data)} bytes")
        
        # Save to disk
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Saved to {filename}")
        
        # Execute callback if provided
        if callback:
            callback()
        
        return image_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {uri}: {e}")
        raise ValueError(f"Download failed: {str(e)}")
    except IOError as e:
        logger.error(f"Failed to save file {filename}: {e}")
        raise ValueError(f"File save failed: {str(e)}")


async def download_async(uri: str, filename: str, callback: Optional[Callable] = None) -> bytes:
    """
    Async version of download function
    
    Args:
        uri: URL to download from
        filename: Local filename to save to
        callback: Optional async callback function
    
    Returns:
        Downloaded image data as bytes
    """
    try:
        logger.info(f"Downloading (async) from {uri}...")
        
        # Download the file
        response = requests.get(uri, timeout=30, stream=True)
        response.raise_for_status()
        
        image_data = response.content
        logger.info(f"Downloaded {len(image_data)} bytes")
        
        # Save to disk
        file_path = Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Saved to {filename}")
        
        # Execute callback if provided
        if callback:
            if callable(callback):
                result = callback()
                # If callback is a coroutine, await it
                if hasattr(result, '__await__'):
                    await result
        
        return image_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {uri}: {e}")
        raise ValueError(f"Download failed: {str(e)}")
    except IOError as e:
        logger.error(f"Failed to save file {filename}: {e}")
        raise ValueError(f"File save failed: {str(e)}")
