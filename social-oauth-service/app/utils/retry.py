"""
Retry logic with exponential backoff
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Type, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = None,
    backoff_seconds: int = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts (defaults to settings)
        backoff_seconds: Initial backoff time in seconds (defaults to settings)
        exceptions: Tuple of exception types to catch and retry
    
    Usage:
        @retry_with_backoff(max_retries=3, backoff_seconds=5)
        def my_function():
            # Function that might fail
            pass
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRY_ATTEMPTS
    if backoff_seconds is None:
        backoff_seconds = settings.RETRY_BACKOFF_SECONDS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            current_backoff = backoff_seconds
            
            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {retry_count}/{max_retries}). "
                        f"Retrying in {current_backoff} seconds. Error: {str(e)}"
                    )
                    
                    time.sleep(current_backoff)
                    # Exponential backoff
                    current_backoff *= 2
            
            # Should never reach here, but just in case
            raise RuntimeError(f"Unexpected exit from retry loop for {func.__name__}")
        
        return wrapper
    return decorator


async def async_retry_with_backoff(
    max_retries: int = None,
    backoff_seconds: int = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Async version of retry_with_backoff decorator
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_seconds: Initial backoff time in seconds
        exceptions: Tuple of exception types to catch and retry
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRY_ATTEMPTS
    if backoff_seconds is None:
        backoff_seconds = settings.RETRY_BACKOFF_SECONDS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            
            retry_count = 0
            current_backoff = backoff_seconds
            
            while retry_count <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {retry_count}/{max_retries}). "
                        f"Retrying in {current_backoff} seconds. Error: {str(e)}"
                    )
                    
                    await asyncio.sleep(current_backoff)
                    current_backoff *= 2
            
            raise RuntimeError(f"Unexpected exit from retry loop for {func.__name__}")
        
        return wrapper
    return decorator
