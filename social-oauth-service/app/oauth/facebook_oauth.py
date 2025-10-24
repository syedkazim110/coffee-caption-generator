"""
Facebook OAuth Provider (via Meta Graph API)
"""
import requests
from typing import Dict, Any
import logging
from urllib.parse import urlencode

from app.oauth.base_provider import BaseOAuthProvider
from app.config import settings

logger = logging.getLogger(__name__)


class FacebookOAuthProvider(BaseOAuthProvider):
    """Facebook OAuth provider using Meta Graph API"""
    
    def __init__(self):
        super().__init__('facebook')
        self.auth_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        self.graph_api_url = "https://graph.facebook.com/v18.0"
    
    def _load_credentials(self):
        """Load Facebook OAuth credentials from settings"""
        self.client_id = settings.FACEBOOK_CLIENT_ID
        self.client_secret = settings.FACEBOOK_CLIENT_SECRET
        self.redirect_uri = settings.FACEBOOK_REDIRECT_URI or f"{settings.BASE_CALLBACK_URL}/api/v1/oauth/facebook/callback"
    
    def get_scopes(self) -> list:
        """Get required Facebook scopes"""
        return [
            'pages_manage_posts',      # Post to pages
            'pages_read_engagement',   # Read engagement metrics
            'pages_show_list',         # List pages user manages
            'pages_read_user_content', # Read page content
            'business_management',     # Access business assets
            'public_profile',          # Basic profile info
            'email'                    # User email (optional)
        ]
    
    def get_authorization_url(self, state: str, **kwargs) -> str:
        """
        Get Facebook authorization URL
        
        Args:
            state: State token for CSRF protection
            **kwargs: Additional parameters
        
        Returns:
            Authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ','.join(self.get_scopes()),
            'response_type': 'code',
            'state': state
        }
        
        url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated Facebook auth URL for state: {state}")
        return url
    
    def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from callback
        
        Returns:
            Token data with access_token, etc.
        """
        try:
            # Step 1: Exchange code for short-lived user access token
            response = requests.get(
                self.token_url,
                params={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'code': code
                },
                timeout=30
            )
            response.raise_for_status()
            short_token_data = response.json()
            
            logger.info("Received short-lived Facebook token")
            
            # Step 2: Exchange for long-lived user access token (60 days)
            long_token_response = requests.get(
                f"{self.graph_api_url}/oauth/access_token",
                params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'fb_exchange_token': short_token_data['access_token']
                },
                timeout=30
            )
            long_token_response.raise_for_status()
            long_token_data = long_token_response.json()
            
            logger.info("Exchanged for long-lived Facebook token")
            
            return {
                'access_token': long_token_data['access_token'],
                'token_type': long_token_data.get('token_type', 'bearer'),
                'expires_in': long_token_data.get('expires_in', 5184000),  # 60 days
                'refresh_token': None  # Facebook uses token exchange, not refresh tokens
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for Facebook token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to obtain Facebook access token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Facebook access token
        
        Note: Facebook uses token exchange, not refresh tokens
        The 'refresh_token' parameter is actually the current access token
        
        Args:
            refresh_token: Current access token to refresh
        
        Returns:
            New token data
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/oauth/access_token",
                params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'fb_exchange_token': refresh_token
                },
                timeout=30
            )
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Facebook access token refreshed successfully")
            
            return {
                'access_token': token_data['access_token'],
                'token_type': token_data.get('token_type', 'bearer'),
                'expires_in': token_data.get('expires_in', 5184000),
                'refresh_token': None
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Facebook token: {e}")
            raise ValueError(f"Failed to refresh Facebook access token: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get Facebook user information and pages
        
        Args:
            access_token: Facebook access token
        
        Returns:
            User information with pages
        """
        try:
            # Get user info
            user_response = requests.get(
                f"{self.graph_api_url}/me",
                params={
                    'fields': 'id,name,email',
                    'access_token': access_token
                },
                timeout=30
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get pages the user manages - with enhanced debugging
            logger.info(f"Fetching pages for user with token: {access_token[:20]}...")
            pages_response = requests.get(
                f"{self.graph_api_url}/me/accounts",
                params={
                    'fields': 'id,name,access_token,category',
                    'access_token': access_token
                },
                timeout=30
            )
            
            logger.info(f"Pages API response status: {pages_response.status_code}")
            logger.info(f"Pages API response length: {len(pages_response.content)} bytes")
            logger.info(f"Pages API raw response: {pages_response.text}")
            
            pages_response.raise_for_status()
            pages_data = pages_response.json()
            
            pages_list = pages_data.get('data', [])
            
            logger.info(f"Retrieved Facebook user info for: {user_data.get('name')}")
            logger.info(f"  - User ID: {user_data.get('id')}")
            logger.info(f"  - Email: {user_data.get('email')}")
            logger.info(f"  - Total pages found: {len(pages_list)}")
            logger.info(f"  - Pages data structure: {pages_data}")
            
            if pages_list:
                for i, page in enumerate(pages_list, 1):
                    logger.info(f"  - Page {i}: {page.get('name')} (ID: {page.get('id')})")
                    logger.info(f"    Category: {page.get('category')}")
                    logger.info(f"    Has access_token: {bool(page.get('access_token'))}")
            else:
                logger.warning(f"  - ⚠️ NO PAGES RETURNED by Facebook API")
                logger.warning(f"  - This could mean:")
                logger.warning(f"    1. User has no Facebook Pages")
                logger.warning(f"    2. Missing required permissions (pages_show_list, pages_manage_posts)")
                logger.warning(f"    3. App not approved for these permissions")
            
            return {
                'user_id': user_data.get('id'),
                'username': user_data.get('name'),
                'email': user_data.get('email'),
                'pages': pages_list,
                'platform': 'facebook'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Facebook user info: {e}")
            raise ValueError(f"Failed to get Facebook user information: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke Facebook access token
        
        Args:
            token: Access token to revoke
        
        Returns:
            True if successful
        """
        try:
            response = requests.delete(
                f"{self.graph_api_url}/me/permissions",
                params={'access_token': token},
                timeout=10
            )
            response.raise_for_status()
            logger.info("Facebook token revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke Facebook token: {e}")
            return False
    
    def get_page_access_token(self, user_access_token: str, page_id: str) -> str:
        """
        Get page access token for posting
        
        Args:
            user_access_token: User's access token
            page_id: Facebook Page ID
        
        Returns:
            Page access token
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/{page_id}",
                params={
                    'fields': 'access_token',
                    'access_token': user_access_token
                },
                timeout=30
            )
            response.raise_for_status()
            page_data = response.json()
            return page_data['access_token']
        except Exception as e:
            logger.error(f"Failed to get page access token: {e}")
            raise


# Global Facebook OAuth provider instance
facebook_oauth = FacebookOAuthProvider()
