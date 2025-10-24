"""
Health Check Routes
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
import logging

from app.config import settings
from app.database import db
from app.utils.temp_image_storage import temp_image_storage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status and component health
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "components": {}
    }
    
    # Check database
    try:
        db_healthy = db.test_connection()
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check OAuth providers
    health_status["components"]["oauth_providers"] = {
        "instagram": "configured" if settings.INSTAGRAM_CLIENT_ID else "not_configured",
        "facebook": "configured" if settings.FACEBOOK_CLIENT_ID else "not_configured"
    }
    
    return health_status


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/Docker
    
    Returns 200 if service is ready to accept requests
    """
    try:
        if not db.test_connection():
            return {"ready": False, "reason": "database_unavailable"}
        
        return {"ready": True}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"ready": False, "reason": str(e)}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker
    
    Returns 200 if service is alive
    """
    return {"alive": True}


@router.get("/temp-images/{filename}")
async def serve_temp_image_get(filename: str):
    """
    Serve temporary images for Instagram posting (GET method)
    
    Args:
        filename: Image filename
    
    Returns:
        Image file
    """
    try:
        # Get image path
        filepath = temp_image_storage.get_image_path(filename)
        
        if not filepath:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get MIME type
        mime_type = temp_image_storage.get_mime_type(filename)
        
        logger.info(f"Serving temp image: {filename} (MIME: {mime_type})")
        
        # Return image file with headers to bypass ngrok browser warning
        return FileResponse(
            path=filepath,
            media_type=mime_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "ngrok-skip-browser-warning": "true",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve temp image {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.head("/temp-images/{filename}")
async def serve_temp_image_head(filename: str):
    """
    Serve temporary image headers only for Instagram's crawler (HEAD method)
    
    Args:
        filename: Image filename
    
    Returns:
        Response with headers only
    """
    try:
        # Get image path
        filepath = temp_image_storage.get_image_path(filename)
        
        if not filepath:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Get MIME type and file size
        mime_type = temp_image_storage.get_mime_type(filename)
        import os
        file_size = os.path.getsize(filepath)
        
        logger.info(f"Serving temp image HEAD: {filename} (MIME: {mime_type}, Size: {file_size})")
        
        # Return headers only
        return Response(
            status_code=200,
            media_type=mime_type,
            headers={
                "Content-Length": str(file_size),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "ngrok-skip-browser-warning": "true",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve temp image HEAD {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
