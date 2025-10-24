"""
Configuration management for OAuth Service
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Social OAuth Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5434
    DB_NAME: str = "oauth_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "oauth_pass"
    
    # Redis (for job queue)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # Security
    ENCRYPTION_KEY: str  # Required - Fernet encryption key
    SERVICE_API_KEY: str = "dev-service-key-change-in-production"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # OAuth Callback URLs (base URL for redirects)
    BASE_CALLBACK_URL: str = "http://localhost:8001"
    
    # Server Base URL (for serving temporary images to Instagram)
    SERVER_BASE_URL: Optional[str] = None  # If None, will use http://localhost:PORT
    
    # ImgBB Image Hosting (for Instagram image uploads)
    IMGBB_API_KEY: Optional[str] = None
    
    # Instagram/Facebook OAuth (Meta)
    INSTAGRAM_CLIENT_ID: Optional[str] = None
    INSTAGRAM_CLIENT_SECRET: Optional[str] = None
    INSTAGRAM_REDIRECT_URI: Optional[str] = None
    
    FACEBOOK_CLIENT_ID: Optional[str] = None
    FACEBOOK_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_REDIRECT_URI: Optional[str] = None
    
    # Twitter/X OAuth
    TWITTER_CLIENT_ID: Optional[str] = None
    TWITTER_CLIENT_SECRET: Optional[str] = None
    TWITTER_REDIRECT_URI: Optional[str] = None
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None
    
    # Token refresh settings
    TOKEN_REFRESH_THRESHOLD_MINUTES: int = 30  # Refresh if expires in < 30 min
    TOKEN_REFRESH_RETRY_ATTEMPTS: int = 3
    
    # Post scheduling
    SCHEDULER_CHECK_INTERVAL_SECONDS: int = 60  # Check for posts every 60 seconds
    MAX_CONCURRENT_POSTS: int = 5
    
    # Rate limiting
    RATE_LIMIT_POSTS_PER_HOUR: int = 50
    RATE_LIMIT_POSTS_PER_DAY: int = 200
    
    # Retry configuration
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_SECONDS: int = 60
    
    # Webhook configuration
    WEBHOOK_SECRET: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        """Get async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
