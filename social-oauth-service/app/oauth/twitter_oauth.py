"""
Twitter/X OAuth Provider (OAuth 2.0 with PKCE)
"""
import requests
from typing import Dict, Any
import logging
from urllib.parse import urlencode
import secrets
import hashlib
import base64

from app.oauth.base_provider import BaseOAuthProvider
from app.config import settings

logger = logging.getLogger(__name__)


class TwitterOAuthProvider(BaseOAuthProvider):
    """Twitter OAuth provider using OAuth 2.0 with PKCE"""
    
    def __init__(self):
        super().__init__('twitter')
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        self.api_url = "https://api.twitter.com/2"
    
    def _load_credentials(self):
        """Load Twitter OAuth credentials from settings"""
        self.client_id = settings.TWITTER_CLIENT_ID
        self.client_secret = settings.TWITTER_CLIENT_SECRET
        self.redirect_uri = settings.TWITTER_REDIRECT_URI or f"{settings.BASE_CALLBACK_URL}/api/v1/oauth/twitter/callback"
    
    def requires_pkce(self) -> bool:
        """Twitter requires PKCE for OAuth 2.0"""
        return True
    
    def get_scopes(self) -> list:
        """Get required Twitter scopes"""
        return [
            'tweet.read',          # Read tweets
            'tweet.write',         # Post tweets
            'tweet.moderate.write',# Moderate tweets
            'users.read',          # Read user profile
            'offline.access',      # Get refresh token
            'media.write'          # Upload media (required for images/videos)
        ]
    
    def get_authorization_url(self, state: str, **kwargs) -> str:
        """
        Get Twitter authorization URL with PKCE
        
        Args:
            state: State token for CSRF protection (with PKCE data stored in database)
            **kwargs: Additional parameters
        
        Returns:
            Authorization URL
        """
        # Get code_challenge from kwargs (passed by parent class via generate_state_token)
        code_challenge = kwargs.get('code_challenge')
        
        if not code_challenge:
            logger.error("No code_challenge provided for Twitter OAuth")
            raise ValueError("PKCE code_challenge is required for Twitter OAuth")
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.get_scopes()),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated Twitter auth URL for state: {state}")
        logger.info(f"Redirect URI: {self.redirect_uri}")
        return url
    
    def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Exchange authorization code for access token using PKCE
        
        Args:
            code: Authorization code from callback
            **kwargs: Must include 'code_verifier' from database
        
        Returns:
            Token data with access_token, refresh_token, etc.
        """
        code_verifier = kwargs.get('code_verifier')
        if not code_verifier:
            logger.error("No code_verifier provided for Twitter token exchange")
            raise ValueError("PKCE code_verifier is required for Twitter token exchange")
        
        logger.info(f"Exchanging Twitter authorization code for access token")
        
        try:
            # Prepare token request
            data = {
                'code': code,
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'code_verifier': code_verifier
            }
            
            # Twitter requires Basic Auth with client credentials
            auth = (self.client_id, self.client_secret)
            
            response = requests.post(
                self.token_url,
                data=data,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully obtained Twitter access token")
            
            return {
                'access_token': token_data['access_token'],
                'token_type': token_data.get('token_type', 'bearer'),
                'expires_in': token_data.get('expires_in', 7200),
                'refresh_token': token_data.get('refresh_token'),
                'scope': token_data.get('scope', ' '.join(self.get_scopes()))
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for Twitter token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to obtain Twitter access token: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Twitter access token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            New token data
        """
        try:
            data = {
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
                'client_id': self.client_id
            }
            
            auth = (self.client_id, self.client_secret)
            
            response = requests.post(
                self.token_url,
                data=data,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Twitter access token refreshed successfully")
            
            return {
                'access_token': token_data['access_token'],
                'token_type': token_data.get('token_type', 'bearer'),
                'expires_in': token_data.get('expires_in', 7200),
                'refresh_token': token_data.get('refresh_token', refresh_token),
                'scope': token_data.get('scope')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Twitter token: {e}")
            raise ValueError(f"Failed to refresh Twitter access token: {str(e)}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get Twitter user information
        
        Args:
            access_token: Twitter access token
        
        Returns:
            User information
        """
        try:
            # Get authenticated user info
            response = requests.get(
                f"{self.api_url}/users/me",
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                params={
                    'user.fields': 'id,name,username,profile_image_url,verified'
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            user_data = data.get('data', {})
            
            logger.info(f"Retrieved Twitter user info for: {user_data.get('username')}")
            logger.info(f"  - User ID: {user_data.get('id')}")
            logger.info(f"  - Name: {user_data.get('name')}")
            logger.info(f"  - Username: @{user_data.get('username')}")
            logger.info(f"  - Verified: {user_data.get('verified', False)}")
            
            return {
                'user_id': user_data.get('id'),
                'username': user_data.get('username'),
                'name': user_data.get('name'),
                'profile_image_url': user_data.get('profile_image_url'),
                'verified': user_data.get('verified', False),
                'platform': 'twitter'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Twitter user info: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise ValueError(f"Failed to get Twitter user information: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke Twitter access token
        
        Args:
            token: Access token to revoke
        
        Returns:
            True if successful
        """
        try:
            data = {
                'token': token,
                'token_type_hint': 'access_token',
                'client_id': self.client_id
            }
            
            auth = (self.client_id, self.client_secret)
            
            response = requests.post(
                f"{self.api_url}/oauth2/revoke",
                data=data,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Twitter token revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke Twitter token: {e}")
            return False


# Global Twitter OAuth provider instance
twitter_oauth = TwitterOAuthProvider()
