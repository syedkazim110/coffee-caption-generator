"""
Publishing Routes - Handle post publishing to social media
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import base64
import re

from app.oauth.instagram_oauth import instagram_oauth
from app.oauth.facebook_oauth import facebook_oauth
from app.publishers.instagram_publisher import instagram_publisher
from app.publishers.facebook_publisher import facebook_publisher
from app.database import db

logger = logging.getLogger(__name__)

router = APIRouter()

# Platform mapping
PROVIDERS = {
    'instagram': instagram_oauth,
    'facebook': facebook_oauth
}

PUBLISHERS = {
    'instagram': instagram_publisher,
    'facebook': facebook_publisher
}


class PublishRequest(BaseModel):
    brand_id: int
    caption: str
    hashtags: Optional[List[str]] = []
    image_url: Optional[str] = None
    platforms: List[str]
    platform_specific: Optional[dict] = {}  # e.g., {"facebook": {"page_id": "123"}}


def decode_base64_image(data_uri: str) -> Optional[bytes]:
    """
    Decode base64 image from data URI
    
    Args:
        data_uri: Data URI string (e.g., 'data:image/png;base64,iVBORw0KG...')
    
    Returns:
        Binary image data or None if invalid
    """
    try:
        # Check if it's a data URI
        if not data_uri.startswith('data:image/'):
            return None
        
        # Extract base64 data after the comma
        match = re.match(r'data:image/[^;]+;base64,(.+)', data_uri)
        if not match:
            logger.error("Invalid data URI format")
            return None
        
        base64_data = match.group(1)
        
        # Decode base64 to binary
        image_bytes = base64.b64decode(base64_data)
        logger.info(f"Successfully decoded base64 image, size: {len(image_bytes)} bytes")
        
        return image_bytes
        
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        return None


class ScheduleRequest(BaseModel):
    brand_id: int
    caption: str
    hashtags: Optional[List[str]] = []
    image_url: Optional[str] = None
    platforms: List[str]
    scheduled_time: datetime
    timezone: str = "UTC"
    approval_required: bool = False
    platform_specific: Optional[dict] = {}


@router.post("/publish")
async def publish_post(request: PublishRequest):
    """
    Publish post immediately to specified platforms
    
    Args:
        request: Publishing request with content and platforms
    
    Returns:
        Publishing results for each platform
    """
    try:
        # Format caption with hashtags
        full_caption = request.caption
        if request.hashtags:
            hashtag_str = ' '.join([f'#{tag.lstrip("#")}' for tag in request.hashtags])
            full_caption = f"{request.caption}\n\n{hashtag_str}"
        
        results = {}
        
        for platform in request.platforms:
            if platform not in PROVIDERS:
                results[platform] = {
                    "success": False,
                    "error": f"Unsupported platform: {platform}"
                }
                continue
            
            try:
                # Get OAuth provider and publisher
                provider = PROVIDERS[platform]
                publisher = PUBLISHERS[platform]
                
                # Check if connected
                connection = provider.get_connection(request.brand_id)
                if not connection:
                    results[platform] = {
                        "success": False,
                        "error": f"Not connected to {platform}. Please authorize the connection first."
                    }
                    continue
                
                # Debug logging
                logger.info(f"Connection for {platform} - Brand {request.brand_id}:")
                logger.info(f"  - Has access_token: {bool(connection.get('access_token'))}")
                logger.info(f"  - Has account_metadata: {bool(connection.get('account_metadata'))}")
                logger.info(f"  - Expires at: {connection.get('expires_at')}")
                
                # Check if token is expired
                if connection.get('expires_at'):
                    expires_at = connection['expires_at']
                    if isinstance(expires_at, str):
                        expires_at = datetime.fromisoformat(expires_at)
                    
                    logger.info(f"  - Current time: {datetime.now()}")
                    logger.info(f"  - Token expired: {datetime.now() >= expires_at}")
                    
                    if datetime.now() >= expires_at:
                        logger.warning(f"Token EXPIRED for {platform}, attempting refresh")
                        try:
                            provider.refresh_token_if_needed(request.brand_id)
                            logger.info(f"Token refresh completed for {platform}")
                        except Exception as refresh_error:
                            logger.error(f"Token refresh FAILED for {platform}: {refresh_error}")
                            results[platform] = {
                                "success": False,
                                "error": f"Token expired (since {expires_at.isoformat()}) and refresh failed: {str(refresh_error)}. Please re-authorize the connection at the OAuth page."
                            }
                            continue
                
                # Refresh token if needed (within threshold)
                try:
                    provider.refresh_token_if_needed(request.brand_id)
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed for {platform}: {refresh_error}")
                    # Continue anyway, might still work
                
                # Get fresh connection with decrypted token
                connection = provider.get_connection(request.brand_id)
                if not connection:
                    results[platform] = {
                        "success": False,
                        "error": f"Failed to retrieve connection after refresh. Please re-authorize."
                    }
                    continue
                
                access_token = connection['access_token']
                
                # Validate we have a token
                if not access_token:
                    results[platform] = {
                        "success": False,
                        "error": f"No access token found for {platform}. Please re-authorize the connection."
                    }
                    continue
                
                # Platform-specific parameters
                kwargs = request.platform_specific.get(platform, {})
                
                # Handle image: detect if it's base64 and convert to binary
                image_url_to_send = request.image_url
                image_data_to_send = None
                
                if request.image_url and request.image_url.startswith('data:image/'):
                    logger.info(f"Detected base64 image for {platform}, converting to binary")
                    image_data_to_send = decode_base64_image(request.image_url)
                    if image_data_to_send:
                        logger.info(f"Successfully converted base64 to binary ({len(image_data_to_send)} bytes)")
                        image_url_to_send = None  # Don't send URL if we have binary data
                    else:
                        logger.warning("Failed to decode base64 image, will attempt URL upload")
                
                # For Instagram, use page_token and add instagram_user_id from connection metadata
                if platform == 'instagram':
                    # Get Instagram account ID and page token from connection metadata
                    logger.info(f"Instagram metadata debug:")
                    logger.info(f"  - connection has 'account_metadata': {'account_metadata' in connection}")
                    
                    if 'account_metadata' in connection:
                        account_metadata = connection.get('account_metadata', {})
                        logger.info(f"  - account_metadata type: {type(account_metadata)}")
                        logger.info(f"  - account_metadata keys: {list(account_metadata.keys()) if isinstance(account_metadata, dict) else 'NOT A DICT'}")
                        
                        # Get Instagram user ID
                        if 'instagram_user_id' not in kwargs:
                            user_id = account_metadata.get('user_id')
                            if user_id:
                                kwargs['instagram_user_id'] = user_id
                                logger.info(f"  - Using stored Instagram user ID: {user_id}")
                        
                        # CRITICAL: Use page_token instead of user access_token for Instagram
                        # Instagram Business posting requires the page token, not the user token
                        all_accounts = account_metadata.get('all_accounts', [])
                        logger.info(f"  - all_accounts present: {bool(all_accounts)}")
                        logger.info(f"  - all_accounts length: {len(all_accounts) if all_accounts else 0}")
                        
                        if all_accounts and len(all_accounts) > 0:
                            logger.info(f"  - first account keys: {list(all_accounts[0].keys())}")
                            page_token = all_accounts[0].get('page_token')
                            if page_token:
                                access_token = page_token
                                logger.info(f"  - ✅ Using Instagram PAGE TOKEN for posting (length: {len(page_token)})")
                            else:
                                logger.error(f"  - ❌ NO page_token found in all_accounts[0]!")
                                results[platform] = {
                                    "success": False,
                                    "error": "Instagram page token not found. Please re-authorize your Instagram account to fix this issue."
                                }
                                continue
                        else:
                            logger.error(f"  - ❌ NO all_accounts in metadata!")
                            results[platform] = {
                                "success": False,
                                "error": "Instagram account data missing. Please re-authorize your Instagram account."
                            }
                            continue
                    else:
                        logger.error(f"  - ❌ NO account_metadata in connection!")
                        results[platform] = {
                            "success": False,
                            "error": "Instagram account metadata missing. Please re-authorize your Instagram account."
                        }
                        continue
                    
                    logger.info(f"  - Final token being used (first 20 chars): {access_token[:20] if access_token else 'NONE'}...")
                
                # For Facebook, we need page_id and page access token
                elif platform == 'facebook':
                    # Get page_id if not provided
                    if 'page_id' not in kwargs:
                        account_metadata = connection.get('account_metadata', {})
                        logger.info(f"Facebook metadata debug:")
                        logger.info(f"  - account_metadata type: {type(account_metadata)}")
                        logger.info(f"  - account_metadata keys: {list(account_metadata.keys()) if isinstance(account_metadata, dict) else 'NOT A DICT'}")
                        
                        pages = account_metadata.get('pages', [])
                        logger.info(f"  - Pages found: {len(pages) if pages else 0}")
                        
                        if pages and len(pages) > 0:
                            kwargs['page_id'] = pages[0]['id']  # Use first page
                            logger.info(f"  - Using page: {pages[0].get('name')} (ID: {pages[0]['id']})")
                        else:
                            logger.error(f"  - ❌ NO pages found in account_metadata!")
                            results[platform] = {
                                "success": False,
                                "error": "No Facebook Pages detected. This could mean:\n" +
                                        "1. You haven't created a Facebook Page yet (you need a Page, not a personal profile)\n" +
                                        "2. The OAuth permissions weren't granted properly\n" +
                                        "3. You need to re-authorize the connection\n\n" +
                                        "Solution: Go to the OAuth page and disconnect, then reconnect your Facebook account. " +
                                        "Make sure to grant all requested permissions during authorization."
                            }
                            continue
                    
                    # Get page access token (required for posting)
                    try:
                        page_access_token = provider.get_page_access_token(
                            user_access_token=access_token,
                            page_id=kwargs['page_id']
                        )
                        access_token = page_access_token
                        logger.info(f"Retrieved page access token for page {kwargs['page_id']}")
                    except Exception as e:
                        results[platform] = {
                            "success": False,
                            "error": f"Failed to get page access token: {str(e)}"
                        }
                        continue
                
                # Add image_data to kwargs if we have it
                if image_data_to_send:
                    kwargs['image_data'] = image_data_to_send
                
                # Publish post
                result = publisher.publish_with_retry(
                    access_token=access_token,
                    caption=full_caption,
                    image_url=image_url_to_send,
                    **kwargs
                )
                
                # Record success
                publisher.record_publish_result(
                    brand_id=request.brand_id,
                    scheduled_post_id=None,
                    result=result,
                    success=True
                )
                
                results[platform] = {
                    "success": True,
                    "post_id": result['post_id'],
                    "url": result['url'],
                    "status": "published"
                }
                
                logger.info(f"Published to {platform} for brand {request.brand_id}: {result['post_id']}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to publish to {platform}: {error_msg}")
                
                # Record failure
                publisher.record_publish_result(
                    brand_id=request.brand_id,
                    scheduled_post_id=None,
                    result={"error": error_msg, "caption": full_caption},
                    success=False
                )
                
                results[platform] = {
                    "success": False,
                    "error": error_msg
                }
        
        # Determine overall success
        overall_success = any(r.get('success', False) for r in results.values())
        
        return {
            "success": overall_success,
            "results": results,
            "brand_id": request.brand_id,
            "published_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_post(request: ScheduleRequest):
    """
    Schedule post for future publishing
    
    Args:
        request: Schedule request with content, platforms, and timing
    
    Returns:
        Scheduled post details
    """
    try:
        # Format caption with hashtags
        full_caption = request.caption
        if request.hashtags:
            hashtag_str = ' '.join([f'#{tag.lstrip("#")}' for tag in request.hashtags])
            full_caption = f"{request.caption}\n\n{hashtag_str}"
        
        # Validate platforms
        for platform in request.platforms:
            if platform not in PROVIDERS:
                raise ValueError(f"Unsupported platform: {platform}")
        
        # Insert scheduled post
        result = db.execute_insert(
            """
            INSERT INTO scheduled_posts (
                brand_id, caption, hashtags, image_url,
                platforms, scheduled_time, timezone,
                approval_required, status, platform_specific_content
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                request.brand_id,
                full_caption,
                request.hashtags,
                request.image_url,
                request.platforms,
                request.scheduled_time,
                request.timezone,
                request.approval_required,
                'pending' if request.approval_required else 'approved',
                request.platform_specific
            )
        )
        
        post = dict(result)
        
        logger.info(f"Scheduled post {post['id']} for brand {request.brand_id}")
        
        return {
            "success": True,
            "post_id": post['id'],
            "brand_id": post['brand_id'],
            "scheduled_time": post['scheduled_time'].isoformat(),
            "status": post['status'],
            "platforms": post['platforms'],
            "approval_required": post['approval_required']
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
async def get_scheduled_posts(
    brand_id: int = Query(..., description="Brand ID"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get scheduled posts for a brand
    
    Args:
        brand_id: Brand ID
        status: Optional status filter (pending, approved, published, failed, cancelled)
    
    Returns:
        List of scheduled posts
    """
    try:
        query = """
            SELECT * FROM scheduled_posts
            WHERE brand_id = %s
        """
        params = [brand_id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY scheduled_time DESC"
        
        results = db.execute_query(query, tuple(params))
        
        posts = []
        for row in results:
            post = dict(row)
            # Format datetime fields
            post['scheduled_time'] = post['scheduled_time'].isoformat()
            post['created_at'] = post['created_at'].isoformat()
            if post.get('published_at'):
                post['published_at'] = post['published_at'].isoformat()
            posts.append(post)
        
        return {
            "success": True,
            "brand_id": brand_id,
            "posts": posts,
            "total": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduled posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{post_id}/approve")
async def approve_post(post_id: int):
    """
    Approve a scheduled post
    
    Args:
        post_id: Scheduled post ID
    
    Returns:
        Updated post status
    """
    try:
        result = db.execute_update(
            """
            UPDATE scheduled_posts
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE id = %s AND approval_required = true AND status = 'pending'
            RETURNING *
            """,
            (post_id,),
            returning=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Post not found or already processed")
        
        post = dict(result)
        
        logger.info(f"Approved post {post_id}")
        
        return {
            "success": True,
            "post_id": post['id'],
            "status": post['status'],
            "approved_at": post['approved_at'].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{post_id}")
async def cancel_post(post_id: int):
    """
    Cancel a scheduled post
    
    Args:
        post_id: Scheduled post ID
    
    Returns:
        Success message
    """
    try:
        result = db.execute_update(
            """
            UPDATE scheduled_posts
            SET status = 'cancelled'
            WHERE id = %s AND status IN ('pending', 'approved')
            RETURNING id
            """,
            (post_id,),
            returning=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Post not found or already processed")
        
        logger.info(f"Cancelled post {post_id}")
        
        return {
            "success": True,
            "message": "Post cancelled",
            "post_id": post_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{post_id}/status")
async def get_post_status(post_id: int):
    """
    Get status of a published post
    
    Args:
        post_id: Post ID from post_history
    
    Returns:
        Post status and metrics
    """
    try:
        result = db.execute_query(
            """
            SELECT * FROM post_history
            WHERE id = %s
            """,
            (post_id,)
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post = dict(result[0])
        
        return {
            "success": True,
            "post_id": post['id'],
            "platform": post['platform'],
            "platform_post_id": post['platform_post_id'],
            "url": post['post_url'],
            "status": post['status'],
            "published_at": post['published_at'].isoformat() if post.get('published_at') else None,
            "engagement": {
                "likes": post.get('likes_count', 0),
                "comments": post.get('comments_count', 0),
                "shares": post.get('shares_count', 0),
                "views": post.get('views_count', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get post status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_publish_history(
    brand_id: int = Query(..., description="Brand ID"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, description="Number of posts to return")
):
    """
    Get publishing history for a brand
    
    Args:
        brand_id: Brand ID
        platform: Optional platform filter
        limit: Maximum number of posts to return
    
    Returns:
        List of published posts
    """
    try:
        query = """
            SELECT * FROM post_history
            WHERE brand_id = %s
        """
        params = [brand_id]
        
        if platform:
            query += " AND platform = %s"
            params.append(platform)
        
        query += " ORDER BY published_at DESC LIMIT %s"
        params.append(limit)
        
        results = db.execute_query(query, tuple(params))
        
        posts = []
        for row in results:
            post = dict(row)
            post['published_at'] = post['published_at'].isoformat() if post.get('published_at') else None
            posts.append(post)
        
        return {
            "success": True,
            "brand_id": brand_id,
            "posts": posts,
            "total": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get publish history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
