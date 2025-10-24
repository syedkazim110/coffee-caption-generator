"""
Base OAuth Provider - abstract class for platform-specific OAuth implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import secrets
import hashlib
import base64
import logging

from app.oauth.token_manager import token_manager
from app.database import db
from app.config import settings

logger = logging.getLogger(__name__)


class BaseOAuthProvider(ABC):
    """Base class for OAuth 2.0 providers"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self._load_credentials()
    
    @abstractmethod
    def _load_credentials(self):
        """Load OAuth credentials from settings (must be implemented by subclasses)"""
        pass
    
    @abstractmethod
    def get_authorization_url(self, state: str, **kwargs) -> str:
        """Get OAuth authorization URL (must be implemented by subclasses)"""
        pass
    
    @abstractmethod
    def exchange_code_for_token(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Returns:
            dict with keys: access_token, refresh_token, expires_in, etc.
        """
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Returns:
            dict with keys: access_token, refresh_token (optional), expires_in
        """
        pass
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from the platform
        
        Returns:
            dict with user information (user_id, username, etc.)
        """
        pass
    
    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """Revoke an access token"""
        pass
    
    def generate_state_token(self, brand_id: int) -> Tuple[str, str]:
        """
        Generate secure state token for OAuth flow with optional PKCE
        
        Args:
            brand_id: Brand ID initiating OAuth
        
        Returns:
            Tuple of (state_token, code_verifier) - code_verifier may be None
        """
        # Generate state token
        state_token = secrets.token_urlsafe(32)
        
        # Generate PKCE code verifier and challenge (if platform requires it)
        code_verifier = None
        code_challenge = None
        
        if self.requires_pkce():
            code_verifier = secrets.token_urlsafe(32)
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
        
        # Store state in database with expiration
        expires_at = datetime.now() + timedelta(minutes=10)  # 10 minute expiration
        
        try:
            db.execute_insert(
                """
                INSERT INTO oauth_states (
                    state_token, platform, brand_id, code_verifier, 
                    code_challenge, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (state_token, self.platform, brand_id, code_verifier, code_challenge, expires_at),
                returning=False
            )
        except Exception as e:
            logger.error(f"Failed to store OAuth state: {e}")
            raise
        
        return state_token, code_verifier
    
    def get_brand_id_from_state(self, state_token: str) -> Optional[int]:
        """
        Retrieve brand_id associated with a state token
        
        Args:
            state_token: State token from OAuth callback
        
        Returns:
            brand_id if found, None otherwise
        """
        try:
            result = db.execute_query(
                """
                SELECT brand_id, expires_at, used 
                FROM oauth_states 
                WHERE state_token = %s AND platform = %s
                """,
                (state_token, self.platform)
            )
            
            if not result or len(result) == 0:
                logger.warning(f"No brand_id found for state token: {state_token}")
                return None
            
            state = dict(result[0])
            
            # Check if already used
            if state['used']:
                logger.warning(f"State token already used: {state_token}")
                return None
            
            # Check expiration
            expires_at = state['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            if datetime.now() > expires_at:
                logger.warning(f"State token expired: {state_token}")
                return None
            
            return state.get('brand_id')
            
        except Exception as e:
            logger.error(f"Failed to retrieve brand_id from state token: {e}")
            return None
    
    def verify_state_token(self, state_token: str, brand_id: int) -> Optional[str]:
        """
        Verify state token and get code_verifier if available
        
        Args:
            state_token: State token from OAuth callback
            brand_id: Brand ID to verify
        
        Returns:
            code_verifier if PKCE is used, None otherwise
        """
        try:
            result = db.execute_query(
                """
                SELECT code_verifier, expires_at, used 
                FROM oauth_states 
                WHERE state_token = %s AND platform = %s AND brand_id = %s
                """,
                (state_token, self.platform, brand_id)
            )
            
            if not result or len(result) == 0:
                logger.warning(f"Invalid state token: {state_token}")
                return None
            
            state = dict(result[0])
            
            # Check if already used
            if state['used']:
                logger.warning(f"State token already used: {state_token}")
                return None
            
            # Check expiration
            expires_at = state['expires_at']
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            
            if datetime.now() > expires_at:
                logger.warning(f"State token expired: {state_token}")
                return None
            
            # Mark as used
            db.execute_update(
                "UPDATE oauth_states SET used = true WHERE state_token = %s",
                (state_token,)
            )
            
            return state.get('code_verifier')
            
        except Exception as e:
            logger.error(f"Failed to verify state token: {e}")
            return None
    
    def requires_pkce(self) -> bool:
        """Override this if platform requires PKCE (Proof Key for Code Exchange)"""
        return False
    
    def get_scopes(self) -> list:
        """Get required OAuth scopes (must be implemented by subclasses)"""
        return []
    
    def save_connection(
        self,
        brand_id: int,
        token_data: Dict[str, Any],
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save OAuth connection to database
        
        Args:
            brand_id: Brand ID
            token_data: Token data from OAuth exchange
            user_info: User information from platform
        
        Returns:
            Saved connection data
        """
        return token_manager.save_connection(
            brand_id=brand_id,
            platform=self.platform,
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_in=token_data.get('expires_in', 3600),
            client_id=self.client_id,
            client_secret=self.client_secret,
            platform_user_id=user_info.get('user_id'),
            platform_username=user_info.get('username'),
            account_metadata=user_info
        )
    
    def get_connection(self, brand_id: int) -> Optional[Dict[str, Any]]:
        """Get OAuth connection for brand"""
        return token_manager.get_connection(brand_id, self.platform)
    
    def refresh_token_if_needed(self, brand_id: int) -> bool:
        """
        Refresh token if it's about to expire
        
        Args:
            brand_id: Brand ID
        
        Returns:
            True if token was refreshed or doesn't need refresh
        """
        connection = self.get_connection(brand_id)
        
        if not connection:
            logger.warning(f"No connection found for brand {brand_id} on {self.platform}")
            return False
        
        if not token_manager.needs_refresh(connection):
            return True  # Token is still valid
        
        # For Facebook/Instagram, the refresh token is actually the current access token
        # that gets exchanged for a new long-lived token
        refresh_token = connection.get('refresh_token')
        if not refresh_token:
            # Fall back to using current access token for platforms that use token exchange
            refresh_token = connection.get('access_token')
            if not refresh_token:
                logger.error(f"No refresh token or access token available for brand {brand_id} on {self.platform}")
                token_manager.mark_error(brand_id, self.platform, "No token available for refresh")
                return False
            logger.info(f"Using access token for refresh (token exchange) for brand {brand_id} on {self.platform}")
        
        try:
            logger.info(f"Refreshing token for brand {brand_id} on {self.platform}")
            new_token_data = self.refresh_access_token(refresh_token)
            
            token_manager.update_tokens(
                brand_id=brand_id,
                platform=self.platform,
                access_token=new_token_data['access_token'],
                refresh_token=new_token_data.get('refresh_token'),  # Some platforms rotate refresh tokens
                expires_in=new_token_data.get('expires_in', 3600)
            )
            
            logger.info(f"Token refreshed successfully for brand {brand_id} on {self.platform}")
            return True
            
        except Exception as e:
            logger.error(f"Token refresh failed for brand {brand_id} on {self.platform}: {e}")
            token_manager.mark_error(brand_id, self.platform, str(e))
            raise  # Re-raise so caller knows it failed
    
    def disconnect(self, brand_id: int) -> bool:
        """Disconnect OAuth connection"""
        connection = self.get_connection(brand_id)
        
        if connection:
            # Try to revoke token on platform side
            try:
                self.revoke_token(connection['access_token'])
            except Exception as e:
                logger.warning(f"Failed to revoke token on platform: {e}")
        
        return token_manager.disconnect(brand_id, self.platform)
