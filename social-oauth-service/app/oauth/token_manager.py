"""
OAuth Token Management - handles storage, retrieval, and refresh
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import json

from app.database import db
from app.utils.encryption import token_encryption
from app.config import settings

logger = logging.getLogger(__name__)


class TokenManager:
    """Manage OAuth tokens with automatic refresh"""
    
    def save_connection(
        self,
        brand_id: int,
        platform: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int,
        client_id: str,
        client_secret: str,
        platform_user_id: Optional[str] = None,
        platform_username: Optional[str] = None,
        account_metadata: Optional[Dict[str, Any]] = None,
        oauth1_access_token: Optional[str] = None,
        oauth1_access_token_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save or update OAuth connection
        
        Args:
            brand_id: Brand ID
            platform: Platform name (instagram, facebook, twitter, linkedin)
            access_token: OAuth access token
            refresh_token: OAuth refresh token (if available)
            expires_in: Token expiration time in seconds
            client_id: OAuth client ID
            client_secret: OAuth client secret
            platform_user_id: User ID on the platform
            platform_username: Username on the platform
            account_metadata: Additional account information
        
        Returns:
            Saved connection data
        """
        try:
            # Calculate expiration timestamp
            expires_at = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
            
            # Encrypt sensitive data
            encrypted_access_token = token_encryption.encrypt_token(access_token)
            encrypted_refresh_token = token_encryption.encrypt_token(refresh_token) if refresh_token else None
            encrypted_client_secret = token_encryption.encrypt_token(client_secret)
            
            # Encrypt OAuth 1.0a credentials if provided
            encrypted_oauth1_token = token_encryption.encrypt_token(oauth1_access_token) if oauth1_access_token else None
            encrypted_oauth1_secret = token_encryption.encrypt_token(oauth1_access_token_secret) if oauth1_access_token_secret else None
            oauth1_enabled = bool(oauth1_access_token and oauth1_access_token_secret)
            
            # Convert account_metadata dict to JSON string for PostgreSQL
            metadata_json = json.dumps(account_metadata) if account_metadata else None
            
            # Log what we're about to save
            if account_metadata:
                logger.info(f"Saving connection for brand {brand_id} on {platform}:")
                logger.info(f"  - Platform user ID: {platform_user_id}")
                logger.info(f"  - Platform username: {platform_username}")
                logger.info(f"  - Metadata keys: {list(account_metadata.keys())}")
                if platform == 'instagram':
                    logger.info(f"  - Has all_accounts: {bool(account_metadata.get('all_accounts'))}")
                    if account_metadata.get('all_accounts'):
                        logger.info(f"  - Number of accounts: {len(account_metadata.get('all_accounts'))}")
                elif platform == 'facebook':
                    logger.info(f"  - Has pages: {bool(account_metadata.get('pages'))}")
                    if account_metadata.get('pages'):
                        logger.info(f"  - Number of pages: {len(account_metadata.get('pages'))}")
            
            # Check if connection already exists
            existing = db.execute_query(
                """
                SELECT id FROM social_connections 
                WHERE brand_id = %s AND platform = %s
                """,
                (brand_id, platform)
            )
            
            if existing and len(existing) > 0:
                # Update existing connection
                result = db.execute_update(
                    """
                    UPDATE social_connections SET
                        access_token = %s,
                        refresh_token = %s,
                        expires_at = %s,
                        client_id = %s,
                        client_secret = %s,
                        platform_user_id = %s,
                        platform_username = %s,
                        account_metadata = %s,
                        oauth1_access_token = %s,
                        oauth1_access_token_secret = %s,
                        oauth1_enabled = %s,
                        is_active = true,
                        connection_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE brand_id = %s AND platform = %s
                    RETURNING *
                    """,
                    (
                        encrypted_access_token,
                        encrypted_refresh_token,
                        expires_at,
                        client_id,
                        encrypted_client_secret,
                        platform_user_id,
                        platform_username,
                        metadata_json,
                        encrypted_oauth1_token,
                        encrypted_oauth1_secret,
                        oauth1_enabled,
                        brand_id,
                        platform
                    ),
                    returning=True
                )
            else:
                # Insert new connection
                result = db.execute_insert(
                    """
                    INSERT INTO social_connections (
                        brand_id, platform, access_token, refresh_token,
                        expires_at, client_id, client_secret,
                        platform_user_id, platform_username, account_metadata,
                        oauth1_access_token, oauth1_access_token_secret, oauth1_enabled
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        brand_id,
                        platform,
                        encrypted_access_token,
                        encrypted_refresh_token,
                        expires_at,
                        client_id,
                        encrypted_client_secret,
                        platform_user_id,
                        platform_username,
                        metadata_json,
                        encrypted_oauth1_token,
                        encrypted_oauth1_secret,
                        oauth1_enabled
                    )
                )
            
            logger.info(f"Saved OAuth connection for brand {brand_id} on {platform}")
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to save connection: {e}")
            raise
    
    def get_connection(self, brand_id: int, platform: str, decrypt: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get OAuth connection for a brand and platform
        
        Args:
            brand_id: Brand ID
            platform: Platform name
            decrypt: Whether to decrypt tokens (default: True)
        
        Returns:
            Connection data with decrypted tokens or None
        """
        try:
            result = db.execute_query(
                """
                SELECT * FROM social_connections
                WHERE brand_id = %s AND platform = %s AND is_active = true
                """,
                (brand_id, platform)
            )
            
            if not result or len(result) == 0:
                return None
            
            connection = dict(result[0])
            
            # Decrypt sensitive fields if requested
            if decrypt:
                connection = token_encryption.decrypt_dict(connection)
            
            # Parse account_metadata from JSON string to dict
            if connection.get('account_metadata'):
                if isinstance(connection['account_metadata'], str):
                    try:
                        connection['account_metadata'] = json.loads(connection['account_metadata'])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse account_metadata JSON: {e}")
                        connection['account_metadata'] = {}
            else:
                connection['account_metadata'] = {}
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to get connection: {e}")
            return None
    
    def get_all_connections(self, brand_id: int, decrypt: bool = False) -> list:
        """Get all OAuth connections for a brand"""
        try:
            results = db.execute_query(
                """
                SELECT * FROM social_connections
                WHERE brand_id = %s AND is_active = true
                ORDER BY created_at DESC
                """,
                (brand_id,)
            )
            
            connections = [dict(row) for row in results]
            
            # Decrypt if requested (but usually not needed for listing)
            if decrypt:
                connections = [token_encryption.decrypt_dict(conn) for conn in connections]
            
            return connections
            
        except Exception as e:
            logger.error(f"Failed to get connections: {e}")
            return []
    
    def needs_refresh(self, connection: Dict[str, Any]) -> bool:
        """
        Check if token needs refresh
        
        Args:
            connection: Connection data
        
        Returns:
            True if token needs refresh
        """
        if not connection.get('expires_at'):
            return False
        
        expires_at = connection['expires_at']
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        threshold = timedelta(minutes=settings.TOKEN_REFRESH_THRESHOLD_MINUTES)
        return datetime.now() + threshold >= expires_at
    
    def update_tokens(
        self,
        brand_id: int,
        platform: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int
    ) -> bool:
        """
        Update tokens after refresh
        
        Args:
            brand_id: Brand ID
            platform: Platform name
            access_token: New access token
            refresh_token: New refresh token (if provided)
            expires_in: Token expiration in seconds
        
        Returns:
            True if successful
        """
        try:
            expires_at = datetime.now() + timedelta(seconds=expires_in) if expires_in else None
            
            encrypted_access_token = token_encryption.encrypt_token(access_token)
            encrypted_refresh_token = token_encryption.encrypt_token(refresh_token) if refresh_token else None
            
            query = """
                UPDATE social_connections SET
                    access_token = %s,
                    expires_at = %s,
                    last_used_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """
            params = [encrypted_access_token, expires_at]
            
            # Update refresh token if provided (Twitter rotates them)
            if encrypted_refresh_token:
                query += ", refresh_token = %s"
                params.append(encrypted_refresh_token)
            
            query += " WHERE brand_id = %s AND platform = %s"
            params.extend([brand_id, platform])
            
            db.execute_update(query, tuple(params))
            
            logger.info(f"Updated tokens for brand {brand_id} on {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update tokens: {e}")
            return False
    
    def mark_error(self, brand_id: int, platform: str, error: str):
        """Mark connection as having an error"""
        try:
            db.execute_update(
                """
                UPDATE social_connections SET
                    connection_error = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE brand_id = %s AND platform = %s
                """,
                (error, brand_id, platform)
            )
            logger.warning(f"Marked connection error for brand {brand_id} on {platform}: {error}")
        except Exception as e:
            logger.error(f"Failed to mark error: {e}")
    
    def disconnect(self, brand_id: int, platform: str) -> bool:
        """Disconnect OAuth connection"""
        try:
            db.execute_update(
                """
                UPDATE social_connections SET
                    is_active = false,
                    updated_at = CURRENT_TIMESTAMP
                WHERE brand_id = %s AND platform = %s
                """,
                (brand_id, platform)
            )
            logger.info(f"Disconnected brand {brand_id} from {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
            return False


# Global token manager instance
token_manager = TokenManager()
