"""
Twitter Publisher - handles posting tweets via Twitter API v2 with OAuth 2.0
Uses v1.1 media upload endpoint with chunked upload support (INIT→APPEND→FINALIZE→STATUS)
Note: Even with Twitter API v2, media uploads must use the v1.1 endpoint
Pure requests implementation for full control
"""
import tweepy
from typing import Dict, Any, Optional
import logging
import requests
from requests_oauthlib import OAuth1Session
from io import BytesIO
import time
import math

from app.publishers.base_publisher import BasePublisher
from app.config import settings

logger = logging.getLogger(__name__)

# Media upload constants
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for chunked upload
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB max for simple image upload
MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512MB max for video
MAX_STATUS_CHECKS = 60  # Maximum status checks for video processing
STATUS_CHECK_INTERVAL = 2  # Seconds between status checks


class TwitterPublisher(BasePublisher):
    """Publisher for Twitter using API v2 with OAuth 2.0 (pure requests implementation)"""
    
    def __init__(self):
        super().__init__('twitter')
        self.api_url = "https://api.twitter.com/2"
    
    def publish_post(
        self,
        access_token: str,
        caption: str,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish a tweet using pure requests (no tweepy dependency issues)
        
        Args:
            access_token: Twitter OAuth access token
            caption: Tweet text (max 280 characters)
            image_url: URL of image to attach (optional)
            image_data: Binary image data (optional)
            **kwargs: Additional parameters (oauth1_token, oauth1_token_secret for media uploads)
        
        Returns:
            dict with tweet_id and url
        """
        try:
            # Validate caption length
            if len(caption) > 280:
                logger.warning(f"Tweet caption exceeds 280 characters ({len(caption)}), truncating...")
                caption = caption[:277] + "..."
            
            # Check if we need to upload media
            media_id = None
            if image_data or (image_url and self.validate_image_url(image_url)):
                # Get OAuth 1.0a credentials from kwargs
                oauth1_token = kwargs.get('oauth1_token')
                oauth1_token_secret = kwargs.get('oauth1_token_secret')
                
                media_id = self._upload_media(
                    access_token,
                    image_url=image_url,
                    image_data=image_data,
                    oauth1_token=oauth1_token,
                    oauth1_token_secret=oauth1_token_secret
                )
            
            # Create the tweet using Twitter API v2
            tweet_url = f"{self.api_url}/tweets"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'text': caption
            }
            
            if media_id:
                payload['media'] = {
                    'media_ids': [media_id]
                }
            
            response = requests.post(
                tweet_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            tweet_id = data['data']['id']
            tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
            
            logger.info(f"Twitter post published successfully: {tweet_id}")
            
            return {
                'post_id': tweet_id,
                'url': tweet_url,
                'platform': 'twitter',
                'caption': caption,
                'image_url': image_url or 'binary_upload' if media_id else None,
                'status': 'published'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to publish Twitter post: {str(e)}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error publishing Twitter post: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _upload_media(
        self,
        access_token: str,
        image_url: Optional[str] = None,
        image_data: Optional[bytes] = None,
        oauth1_token: Optional[str] = None,
        oauth1_token_secret: Optional[str] = None
    ) -> str:
        """
        Upload media using Twitter API v1.1 chunked upload with OAuth 1.0a
        (INIT→APPEND→FINALIZE→STATUS)
        
        NOTE: Twitter's v1.1 media upload endpoint REQUIRES OAuth 1.0a authentication.
        OAuth 2.0 Bearer tokens will result in 403 Forbidden errors.
        
        Args:
            access_token: Twitter OAuth 2.0 access token (not used for media upload, kept for compatibility)
            image_url: URL of image (optional)
            image_data: Binary image data (optional)
            oauth1_token: OAuth 1.0a access token (required for media upload)
            oauth1_token_secret: OAuth 1.0a access token secret (required for media upload)
        
        Returns:
            media_id string
        """
        try:
            # Get image data if URL is provided
            if image_url and not image_data:
                logger.info(f"Downloading image from URL: {image_url}")
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_data = response.content
            
            if not image_data:
                raise ValueError("No image data provided for media upload")
            
            # Check for OAuth 1.0a credentials
            if not oauth1_token or not oauth1_token_secret:
                error_msg = (
                    "OAuth 1.0a credentials required for Twitter media upload. "
                    "The v1.1 media upload endpoint does not support OAuth 2.0 Bearer tokens. "
                    "Please provide oauth1_token and oauth1_token_secret."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            total_bytes = len(image_data)
            media_type = 'image/jpeg'  # Default, could be enhanced to detect actual type
            
            logger.info(f"Starting chunked media upload using v1.1 endpoint with OAuth 1.0a ({total_bytes} bytes)")
            
            # Create OAuth 1.0a session
            oauth = OAuth1Session(
                settings.TWITTER_API_KEY,
                client_secret=settings.TWITTER_API_SECRET,
                resource_owner_key=oauth1_token,
                resource_owner_secret=oauth1_token_secret
            )
            
            upload_url = "https://upload.twitter.com/1.1/media/upload.json"
            
            # === STEP 1: INIT ===
            logger.info("Step 1: INIT - Creating upload session")
            
            init_data = {
                'command': 'INIT',
                'total_bytes': total_bytes,
                'media_type': media_type
            }
            
            response = oauth.post(
                upload_url,
                data=init_data,
                timeout=30
            )
            
            response.raise_for_status()
            init_result = response.json()
            media_id = str(init_result['media_id_string'])
            
            logger.info(f"✓ INIT successful - media_id: {media_id}")
            
            # === STEP 2: APPEND ===
            logger.info("Step 2: APPEND - Uploading media chunks")
            
            num_chunks = math.ceil(total_bytes / CHUNK_SIZE)
            logger.info(f"Uploading {num_chunks} chunk(s)")
            
            for chunk_index in range(num_chunks):
                start = chunk_index * CHUNK_SIZE
                end = min(start + CHUNK_SIZE, total_bytes)
                chunk = image_data[start:end]
                
                logger.info(f"Uploading chunk {chunk_index}/{num_chunks - 1} ({len(chunk)} bytes)")
                
                append_data = {
                    'command': 'APPEND',
                    'media_id': media_id,
                    'segment_index': chunk_index
                }
                
                files = {
                    'media': (f'chunk_{chunk_index}', BytesIO(chunk), 'application/octet-stream')
                }
                
                response = oauth.post(
                    upload_url,
                    data=append_data,
                    files=files,
                    timeout=60
                )
                
                response.raise_for_status()
                logger.info(f"✓ Chunk {chunk_index} uploaded")
            
            logger.info("✓ APPEND complete - all chunks uploaded")
            
            # === STEP 3: FINALIZE ===
            logger.info("Step 3: FINALIZE - Finalizing upload")
            
            finalize_data = {
                'command': 'FINALIZE',
                'media_id': media_id
            }
            
            response = oauth.post(
                upload_url,
                data=finalize_data,
                timeout=30
            )
            
            response.raise_for_status()
            finalize_result = response.json()
            
            logger.info("✓ FINALIZE successful")
            
            # === STEP 4: STATUS (if processing required) ===
            processing_info = finalize_result.get('processing_info')
            
            if processing_info:
                state = processing_info.get('state')
                logger.info(f"Step 4: STATUS - Media processing required (state: {state})")
                
                # Poll for processing completion
                check_count = 0
                while state in ['pending', 'in_progress'] and check_count < MAX_STATUS_CHECKS:
                    check_after_secs = processing_info.get('check_after_secs', STATUS_CHECK_INTERVAL)
                    logger.info(f"Waiting {check_after_secs}s for processing... (check {check_count + 1}/{MAX_STATUS_CHECKS})")
                    
                    time.sleep(check_after_secs)
                    
                    # Check status
                    status_params = {
                        'command': 'STATUS',
                        'media_id': media_id
                    }
                    
                    response = oauth.get(
                        upload_url,
                        params=status_params,
                        timeout=30
                    )
                    
                    response.raise_for_status()
                    status_result = response.json()
                    processing_info = status_result.get('processing_info', {})
                    state = processing_info.get('state')
                    
                    check_count += 1
                
                if state == 'succeeded':
                    logger.info("✓ STATUS check complete - media processing succeeded")
                elif state == 'failed':
                    error = processing_info.get('error', {})
                    raise ValueError(f"Media processing failed: {error}")
                else:
                    logger.warning(f"Media processing state unclear: {state}")
            else:
                logger.info("No processing required (image ready immediately)")
            
            logger.info(f"✅ Media upload complete - media_id: {media_id}")
            return media_id
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to upload media to Twitter: {str(e)}"
            logger.error(error_msg)
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during media upload: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def delete_post(self, access_token: str, post_id: str) -> bool:
        """
        Delete a tweet
        
        Args:
            access_token: Twitter OAuth access token
            post_id: Tweet ID
        
        Returns:
            True if successful
        """
        try:
            client = self._create_client(access_token)
            client.delete_tweet(post_id)
            logger.info(f"Twitter post {post_id} deleted successfully")
            return True
        except tweepy.TweepyException as e:
            logger.error(f"Failed to delete Twitter post: {e}")
            return False
    
    def get_post_status(self, access_token: str, post_id: str) -> Dict[str, Any]:
        """
        Get tweet status and metrics
        
        Args:
            access_token: Twitter OAuth access token
            post_id: Tweet ID
        
        Returns:
            Tweet metrics and status
        """
        try:
            client = self._create_client(access_token)
            
            # Get tweet with public metrics
            tweet = client.get_tweet(
                post_id,
                tweet_fields=['created_at', 'public_metrics', 'text'],
                expansions=['author_id']
            )
            
            tweet_data = tweet.data
            metrics = tweet_data.public_metrics or {}
            
            return {
                'post_id': tweet_data.id,
                'url': f"https://twitter.com/i/web/status/{tweet_data.id}",
                'text': tweet_data.text,
                'created_at': str(tweet_data.created_at) if tweet_data.created_at else None,
                'retweets': metrics.get('retweet_count', 0),
                'likes': metrics.get('like_count', 0),
                'replies': metrics.get('reply_count', 0),
                'quotes': metrics.get('quote_count', 0),
                'impressions': metrics.get('impression_count', 0),
                'status': 'published'
            }
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get Twitter post status: {e}")
            return {
                'post_id': post_id,
                'status': 'unknown',
                'error': str(e)
            }
    
    def get_user_tweets(
        self,
        access_token: str,
        user_id: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Get user's recent tweets
        
        Args:
            access_token: Twitter OAuth access token
            user_id: Twitter user ID
            max_results: Maximum number of tweets to retrieve (5-100)
        
        Returns:
            List of tweets
        """
        try:
            client = self._create_client(access_token)
            
            tweets = client.get_users_tweets(
                user_id,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'public_metrics', 'text']
            )
            
            tweet_list = []
            if tweets.data:
                for tweet in tweets.data:
                    metrics = tweet.public_metrics or {}
                    tweet_list.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': str(tweet.created_at) if tweet.created_at else None,
                        'likes': metrics.get('like_count', 0),
                        'retweets': metrics.get('retweet_count', 0),
                        'replies': metrics.get('reply_count', 0)
                    })
            
            return {
                'tweets': tweet_list,
                'count': len(tweet_list)
            }
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get user tweets: {e}")
            return {
                'tweets': [],
                'count': 0,
                'error': str(e)
            }
    
    def search_tweets(
        self,
        access_token: str,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for tweets
        
        Args:
            access_token: Twitter OAuth access token
            query: Search query
            max_results: Maximum number of results (10-100)
        
        Returns:
            List of matching tweets
        """
        try:
            client = self._create_client(access_token)
            
            tweets = client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'public_metrics', 'author_id']
            )
            
            tweet_list = []
            if tweets.data:
                for tweet in tweets.data:
                    metrics = tweet.public_metrics or {}
                    tweet_list.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'author_id': tweet.author_id,
                        'created_at': str(tweet.created_at) if tweet.created_at else None,
                        'likes': metrics.get('like_count', 0),
                        'retweets': metrics.get('retweet_count', 0)
                    })
            
            return {
                'tweets': tweet_list,
                'count': len(tweet_list),
                'query': query
            }
        except tweepy.TweepyException as e:
            logger.error(f"Failed to search tweets: {e}")
            return {
                'tweets': [],
                'count': 0,
                'query': query,
                'error': str(e)
            }


# Global Twitter publisher instance
twitter_publisher = TwitterPublisher()
