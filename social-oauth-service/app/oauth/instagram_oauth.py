"""
Instagram OAuth Provider (via Facebook Graph API)
Instagram Graph API is accessed through Facebook OAuth
"""
import requests
from typing import Dict, Any
import logging
from urllib.parse import urlencode

from app.oauth.base_provider import BaseOAuthProvider
from app.config import settings

logger = logging.getLogger(__name__)


class InstagramOAuthProvider(BaseOAuthProvider):
    """Instagram OAuth provider using Facebook Graph API"""
    
    def __init__(self):
        super().__init__('instagram')
        # Instagram uses Facebook OAuth system
        self.auth_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        self.graph_api_url = "https://graph.facebook.com/v18.0"
    
    def _load_credentials(self):
        """Load Instagram OAuth credentials from settings"""
        # Instagram Graph API uses main Facebook app credentials
        self.client_id = settings.FACEBOOK_CLIENT_ID
        self.client_secret = settings.FACEBOOK_CLIENT_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI or f"{settings.BASE_CALLBACK_URL}/api/v1/oauth/instagram/callback"
    
    def get_scopes(self) -> list:
        """Get required Instagram scopes via Facebook Login"""
        return [
            'instagram_basic',
            'instagram_content_publish',
            'instagram_manage_comments',
            'instagram_manage_insights',
            'pages_show_list',
            'pages_read_engagement',
            'business_management',
            'public_profile'
        ]
    
    def get_authorization_url(self, state: str, **kwargs) -> str:
        """
        Get Instagram authorization URL (via Facebook OAuth)
        
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
        logger.info(f"Generated Instagram auth URL (via Facebook) for state: {state}")
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
            # Step 1: Exchange code for short-lived Facebook token
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
            
            logger.info("Received short-lived token for Instagram (via Facebook)")
            
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
            
            logger.info("Exchanged for long-lived token for Instagram access")
            
            return {
                'access_token': long_token_data['access_token'],
                'token_type': long_token_data.get('token_type', 'bearer'),
                'expires_in': long_token_data.get('expires_in', 5184000),  # 60 days
                'refresh_token': None  # Facebook uses token exchange, not refresh tokens
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for Instagram token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to obtain Instagram access token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Instagram access token
        
        Note: Uses Facebook token exchange system
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
            
            logger.info("Instagram access token refreshed successfully")
            
            return {
                'access_token': token_data['access_token'],
                'token_type': token_data.get('token_type', 'bearer'),
                'expires_in': token_data.get('expires_in', 5184000),
                'refresh_token': None
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Instagram token: {e}")
            raise ValueError(f"Failed to refresh Instagram access token: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get Instagram user information via Facebook Pages
        
        Args:
            access_token: Facebook/Instagram access token
        
        Returns:
            User information with Instagram Business Account details
        """
        try:
            # Get user's Facebook Pages
            pages_response = requests.get(
                f"{self.graph_api_url}/me/accounts",
                params={
                    'fields': 'id,name,access_token,instagram_business_account',
                    'access_token': access_token
                },
                timeout=30
            )
            pages_response.raise_for_status()
            pages_data = pages_response.json()
            
            # Find pages with Instagram Business Account connected
            instagram_accounts = []
            for page in pages_data.get('data', []):
                if 'instagram_business_account' in page:
                    ig_account_id = page['instagram_business_account']['id']
                    page_token = page.get('access_token', access_token)
                    
                    # Get Instagram account details
                    ig_response = requests.get(
                        f"{self.graph_api_url}/{ig_account_id}",
                        params={
                            'fields': 'id,username,name,profile_picture_url,followers_count,media_count',
                            'access_token': page_token
                        },
                        timeout=30
                    )
                    
                    if ig_response.status_code == 200:
                        ig_data = ig_response.json()
                        instagram_accounts.append({
                            'ig_account_id': ig_account_id,
                            'username': ig_data.get('username'),
                            'name': ig_data.get('name'),
                            'profile_picture_url': ig_data.get('profile_picture_url'),
                            'followers_count': ig_data.get('followers_count'),
                            'media_count': ig_data.get('media_count'),
                            'page_id': page['id'],
                            'page_name': page['name'],
                            'page_token': page_token
                        })
            
            if not instagram_accounts:
                raise ValueError("No Instagram Business Account found connected to your Facebook Pages. Please connect an Instagram Business Account to your Facebook Page.")
            
            # Use the first Instagram account found
            primary_account = instagram_accounts[0]
            
            logger.info(f"Retrieved Instagram account info for: {primary_account['username']}")
            logger.info(f"  - Instagram Account ID: {primary_account['ig_account_id']}")
            logger.info(f"  - Page ID: {primary_account['page_id']}")
            logger.info(f"  - Has page_token: {bool(primary_account.get('page_token'))}")
            logger.info(f"  - Total accounts found: {len(instagram_accounts)}")
            
            return {
                'user_id': primary_account['ig_account_id'],
                'username': primary_account['username'],
                'account_name': primary_account.get('name'),
                'profile_picture': primary_account.get('profile_picture_url'),
                'followers_count': primary_account.get('followers_count'),
                'media_count': primary_account.get('media_count'),
                'page_id': primary_account['page_id'],
                'page_name': primary_account['page_name'],
                'page_token': primary_account['page_token'],
                'all_accounts': instagram_accounts,
                'platform': 'instagram'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Instagram user info: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to get Instagram user information: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke Instagram access token (via Facebook)
        
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
            logger.info("Instagram token revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke Instagram token: {e}")
            return False
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validate if an Instagram access token is still valid
        
        Args:
            access_token: Token to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            response = requests.get(
                f"{self.graph_api_url}/me",
                params={'access_token': access_token},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


# Global Instagram OAuth provider instance
instagram_oauth = InstagramOAuthProvider()
