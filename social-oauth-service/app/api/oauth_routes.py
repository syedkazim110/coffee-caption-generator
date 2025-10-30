"""
OAuth Routes - Handle OAuth flows and connections
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import logging

from app.oauth.instagram_oauth import instagram_oauth
from app.oauth.facebook_oauth import facebook_oauth
from app.oauth.twitter_oauth import twitter_oauth
from app.oauth.token_manager import token_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Platform provider mapping
PROVIDERS = {
    'instagram': instagram_oauth,
    'facebook': facebook_oauth,
    'twitter': twitter_oauth
}


class AuthorizeRequest(BaseModel):
    brand_id: int


class ConnectionsQuery(BaseModel):
    brand_id: int


@router.post("/{platform}/authorize")
async def initiate_oauth(platform: str, request: AuthorizeRequest):
    """
    Initiate OAuth authorization flow
    
    Args:
        platform: Platform name (instagram/facebook/twitter)
        request: Authorization request with brand_id
    
    Returns:
        Authorization URL and state token
    """
    if platform not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    provider = PROVIDERS[platform]
    
    try:
        # Generate state token with PKCE if needed
        state_token, code_verifier = provider.generate_state_token(request.brand_id)
        
        # For platforms requiring PKCE, retrieve code_challenge from database
        kwargs = {}
        if provider.requires_pkce() and code_verifier:
            # Get code_challenge from database (stored by generate_state_token)
            from app.database import db
            result = db.execute_query(
                "SELECT code_challenge FROM oauth_states WHERE state_token = %s",
                (state_token,)
            )
            if result and len(result) > 0:
                kwargs['code_challenge'] = result[0]['code_challenge']
                logger.info(f"Retrieved code_challenge for {platform} PKCE flow")
        
        # Get authorization URL
        auth_url = provider.get_authorization_url(state_token, **kwargs)
        
        logger.info(f"OAuth initiated for {platform}, brand {request.brand_id}")
        logger.info(f"Authorization URL: {auth_url[:100]}...")  # Log first 100 chars
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "state": state_token,
            "platform": platform
        }
    except Exception as e:
        logger.error(f"Failed to initiate OAuth for {platform}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    brand_id: Optional[int] = Query(None, description="Brand ID (optional, retrieved from state if not provided)")
):
    """
    Handle OAuth callback from platform
    
    This endpoint is called by the platform after user authorization.
    Returns an HTML response with JavaScript to notify parent window.
    
    Args:
        platform: Platform name
        code: Authorization code
        state: State token for CSRF protection
        brand_id: Brand ID (optional - will be retrieved from state token if not provided)
    
    Returns:
        HTML response with success or error message
    """
    if platform not in PROVIDERS:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error: Unsupported platform '{platform}'</h1>
            <script>
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth_error',
                        platform: '{platform}',
                        error: 'Unsupported platform'
                    }}, '*');
                }}
                setTimeout(() => window.close(), 3000);
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)
    
    provider = PROVIDERS[platform]
    
    try:
        # Retrieve brand_id from state token if not provided in query params
        if not brand_id:
            brand_id = provider.get_brand_id_from_state(state)
            if not brand_id:
                raise ValueError("Invalid or expired state token - could not retrieve brand_id")
            logger.info(f"Retrieved brand_id {brand_id} from state token")
        
        # Verify state token
        code_verifier = provider.verify_state_token(state, brand_id)
        if code_verifier is None and provider.requires_pkce():
            raise ValueError("Invalid or expired state token")
        
        # Exchange code for tokens
        token_data = provider.exchange_code_for_token(
            code,
            code_verifier=code_verifier
        )
        
        # Get user info
        user_info = provider.get_user_info(token_data['access_token'])
        
        # Save connection
        connection = provider.save_connection(brand_id, token_data, user_info)
        
        logger.info(f"OAuth completed for {platform}, brand {brand_id}")
        
        # Return success page with JavaScript to notify parent window
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Successful</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                }}
                .success-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Authorization Successful!</h1>
                <p>Your {platform.title()} account has been connected.</p>
                <p>You can close this window now.</p>
            </div>
            <script>
                // Send success message to parent window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth_success',
                        platform: '{platform}',
                        brand_id: {brand_id}
                    }}, '*');
                }}
                // Auto-close after 2 seconds
                setTimeout(() => window.close(), 2000);
            </script>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"OAuth callback failed for {platform}: {e}")
        
        # Return error page with JavaScript to notify parent window
        import html
        import json
        error_message_html = html.escape(str(e))
        error_message_json = json.dumps(str(e))  # Properly escape for JavaScript
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    max-width: 500px;
                    padding: 20px;
                }}
                .error-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                .error-details {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">✗</div>
                <h1>Authorization Failed</h1>
                <p>There was an error connecting your {platform.title()} account.</p>
                <div class="error-details">{error_message_html}</div>
                <p>Please try again or contact support if the issue persists.</p>
            </div>
            <script>
                // Send error message to parent window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'oauth_error',
                        platform: '{platform}',
                        error: {error_message_json}
                    }}, '*');
                }}
                // Auto-close after 3 seconds
                setTimeout(() => window.close(), 3000);
            </script>
        </body>
        </html>
        """, status_code=400)


@router.get("/{platform}/callback-old")
async def oauth_callback_old(
    platform: str,
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    brand_id: int = Query(..., description="Brand ID")
):
    """
    OLD callback handler - kept for reference
    This shows the success page directly instead of redirecting
    """
    if platform not in PROVIDERS:
        return HTMLResponse(
            content=f"<h1>Error: Unsupported platform '{platform}'</h1>",
            status_code=400
        )
    
    provider = PROVIDERS[platform]
    
    try:
        # Verify state token
        code_verifier = provider.verify_state_token(state, brand_id)
        if code_verifier is None and provider.requires_pkce():
            raise ValueError("Invalid or expired state token")
        
        # Exchange code for tokens
        token_data = provider.exchange_code_for_token(
            code,
            code_verifier=code_verifier
        )
        
        # Get user info
        user_info = provider.get_user_info(token_data['access_token'])
        
        # Save connection
        connection = provider.save_connection(brand_id, token_data, user_info)
        
        logger.info(f"OAuth completed for {platform}, brand {brand_id}")
        
        # Return success page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Successful</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                    max-width: 500px;
                }}
                .success-icon {{
                    font-size: 64px;
                    color: #4CAF50;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #666;
                    margin-bottom: 20px;
                }}
                .details {{
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .button {{
                    display: inline-block;
                    background: #667eea;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 5px;
                    text-decoration: none;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Authorization Successful!</h1>
                <p>Your {platform.title()} account has been connected successfully.</p>
                <div class="details">
                    <strong>Platform:</strong> {platform.title()}<br>
                    <strong>Account:</strong> {user_info.get('username', 'N/A')}<br>
                    <strong>Status:</strong> <span style="color: #4CAF50;">Connected</span>
                </div>
                <p>You can now close this window and return to the application.</p>
                <a href="#" class="button" onclick="window.close()">Close Window</a>
            </div>
            <script>
                // Auto-close after 5 seconds
                setTimeout(() => window.close(), 5000);
            </script>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"OAuth callback failed for {platform}: {e}")
        
        # Return error page
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authorization Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 64px;
                    color: #f5576c;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #666;
                }}
                .error-details {{
                    background: #fee;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                    color: #c00;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">✗</div>
                <h1>Authorization Failed</h1>
                <p>There was an error connecting your {platform.title()} account.</p>
                <div class="error-details">
                    {str(e)}
                </div>
                <p>Please try again or contact support if the issue persists.</p>
            </div>
        </body>
        </html>
        """, status_code=400)


@router.get("/connections")
async def get_connections(brand_id: int = Query(..., description="Brand ID")):
    """
    Get all OAuth connections for a brand
    
    Args:
        brand_id: Brand ID
    
    Returns:
        List of connected platforms
    """
    try:
        connections = token_manager.get_all_connections(brand_id, decrypt=False)
        
        # Format connections for response (hide sensitive data)
        formatted_connections = []
        for conn in connections:
            formatted_connections.append({
                "platform": conn['platform'],
                "platform_username": conn.get('platform_username'),
                "account_name": conn.get('account_name'),
                "is_active": conn['is_active'],
                "expires_at": conn.get('expires_at').isoformat() if conn.get('expires_at') else None,
                "connected_at": conn['created_at'].isoformat(),
                "last_used": conn.get('last_used_at').isoformat() if conn.get('last_used_at') else None,
                "connection_error": conn.get('connection_error')
            })
        
        return {
            "success": True,
            "brand_id": brand_id,
            "connections": formatted_connections,
            "total": len(formatted_connections)
        }
    except Exception as e:
        logger.error(f"Failed to get connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{platform}/disconnect")
async def disconnect_platform(
    platform: str,
    brand_id: int = Query(..., description="Brand ID")
):
    """
    Disconnect OAuth connection
    
    Args:
        platform: Platform name
        brand_id: Brand ID
    
    Returns:
        Success message
    """
    if platform not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    provider = PROVIDERS[platform]
    
    try:
        success = provider.disconnect(brand_id)
        
        if success:
            logger.info(f"Disconnected {platform} for brand {brand_id}")
            return {
                "success": True,
                "message": f"Disconnected from {platform}",
                "platform": platform,
                "brand_id": brand_id
            }
        else:
            raise HTTPException(status_code=404, detail="Connection not found")
            
    except Exception as e:
        logger.error(f"Failed to disconnect {platform}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{platform}/status")
async def get_connection_status(
    platform: str,
    brand_id: int = Query(..., description="Brand ID")
):
    """
    Check OAuth connection status
    
    Args:
        platform: Platform name
        brand_id: Brand ID
    
    Returns:
        Connection status
    """
    if platform not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
    
    provider = PROVIDERS[platform]
    
    try:
        connection = provider.get_connection(brand_id)
        
        if not connection:
            return {
                "success": True,
                "platform": platform,
                "connected": False
            }
        
        # Check if token needs refresh
        needs_refresh = token_manager.needs_refresh(connection)
        
        return {
            "success": True,
            "platform": platform,
            "connected": True,
            "account": connection.get('platform_username'),
            "expires_at": connection.get('expires_at').isoformat() if connection.get('expires_at') else None,
            "needs_refresh": needs_refresh,
            "is_active": connection.get('is_active'),
            "error": connection.get('connection_error')
        }
    except Exception as e:
        logger.error(f"Failed to check connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
