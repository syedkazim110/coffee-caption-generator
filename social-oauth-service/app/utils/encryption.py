"""
Token encryption and decryption utilities
"""
from cryptography.fernet import Fernet
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Handle encryption and decryption of OAuth tokens"""
    
    def __init__(self):
        """Initialize with encryption key from settings"""
        try:
            # Validate encryption key format
            key = settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY
            self.cipher = Fernet(key)
            logger.info("Token encryption initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError(f"Invalid encryption key. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an OAuth token
        
        Args:
            token: Plain text token to encrypt
            
        Returns:
            Encrypted token as string
        """
        if not token:
            return ""
        
        try:
            token_bytes = token.encode('utf-8')
            encrypted_bytes = self.cipher.encrypt(token_bytes)
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt an OAuth token
        
        Args:
            encrypted_token: Encrypted token string
            
        Returns:
            Decrypted plain text token or None if decryption fails
        """
        if not encrypted_token:
            return None
        
        try:
            encrypted_bytes = encrypted_token.encode('utf-8')
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt sensitive fields in a dictionary
        
        Args:
            data: Dictionary with tokens to encrypt
            
        Returns:
            Dictionary with encrypted tokens
        """
        sensitive_fields = ['access_token', 'refresh_token', 'client_secret']
        encrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_token(encrypted_data[field])
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt sensitive fields in a dictionary
        
        Args:
            data: Dictionary with encrypted tokens
            
        Returns:
            Dictionary with decrypted tokens
        """
        sensitive_fields = ['access_token', 'refresh_token', 'client_secret']
        decrypted_data = data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt_token(decrypted_data[field])
        
        return decrypted_data
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet encryption key"""
        return Fernet.generate_key().decode()


# Global encryption instance
token_encryption = TokenEncryption()


def generate_encryption_key():
    """Helper function to generate a new encryption key"""
    key = Fernet.generate_key()
    print(f"Generated encryption key: {key.decode()}")
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    return key.decode()


if __name__ == "__main__":
    # Generate key when run directly
    generate_encryption_key()
