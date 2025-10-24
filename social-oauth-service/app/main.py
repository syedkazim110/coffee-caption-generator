"""
Main FastAPI Application for OAuth Service
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
from typing import Optional

from app.config import settings
from app.database import db
from app.api import oauth_routes, publish_routes, health_routes
from app.utils.temp_image_storage import temp_image_storage

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="OAuth 2.0 Service for Social Media Platforms (Instagram & Facebook)",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key Authentication Dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify service-to-service API key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Check if API key is valid
    result = db.execute_query(
        "SELECT is_active FROM service_api_keys WHERE api_key = %s",
        (x_api_key,)
    )
    
    if not result or len(result) == 0 or not result[0]['is_active']:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Update last used timestamp
    db.execute_update(
        "UPDATE service_api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE api_key = %s",
        (x_api_key,)
    )
    
    return x_api_key


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Test database connection
    if db.test_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.error("✗ Database connection failed")
        raise RuntimeError("Cannot connect to database")
    
    # Clean up old temporary images
    try:
        temp_image_storage.cleanup_old_images(max_age_hours=1)
        logger.info("✓ Cleaned up old temporary images")
    except Exception as e:
        logger.warning(f"Failed to cleanup old temp images: {e}")
    
    logger.info(f"✓ OAuth Service ready on {settings.HOST}:{settings.PORT}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down OAuth Service")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return RedirectResponse(url="/docs")


# Include routers
app.include_router(
    health_routes.router,
    tags=["Health"]
)

app.include_router(
    oauth_routes.router,
    prefix="/api/v1/oauth",
    tags=["OAuth"],
    dependencies=[]  # OAuth endpoints don't require API key for callbacks
)

app.include_router(
    publish_routes.router,
    prefix="/api/v1/posts",
    tags=["Publishing"],
    dependencies=[Depends(verify_api_key)]  # Publishing requires API key
)


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "success": False,
        "error": "Endpoint not found",
        "detail": str(exc)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc) if settings.DEBUG else "An error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
