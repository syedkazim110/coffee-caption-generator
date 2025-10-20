from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from llm_rag_caption_generator import LLMRAGCaptionGenerator
from brand_manager import BrandManager
from platform_strategies import PlatformStrategy
import os
from dotenv import load_dotenv
import logging
import base64
from PIL import Image
from io import BytesIO
import requests
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Coffee Caption Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize caption generator with environment variables
logger.info("Initializing caption generator...")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
logger.info(f"Using Ollama URL: {OLLAMA_URL}")
logger.info(f"Using Ollama Model: {OLLAMA_MODEL}")
caption_generator = LLMRAGCaptionGenerator(
    ollama_url=OLLAMA_URL,
    ollama_model=OLLAMA_MODEL
)

# Initialize brand manager and platform strategy
logger.info("Initializing brand manager...")
brand_manager = BrandManager()

logger.info("Initializing platform strategy...")
platform_strategy = PlatformStrategy()

# Hugging Face Inference API Configuration
# Using verified working models with fallback options
HF_PRIMARY_MODEL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
HF_FALLBACK_MODEL = "https://api-inference.huggingface.co/models/prompthero/openjourney"
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

class PostRequest(BaseModel):
    keyword: Optional[str] = None
    brand_id: Optional[int] = None
    platform: Optional[str] = 'instagram'
    scenario: Optional[str] = None

class BrandCreateRequest(BaseModel):
    brand_name: str
    brand_type: str
    product_nature: str
    industry: str
    target_audience: str
    content_language: Optional[str] = 'English (US)'
    voice_profile: Optional[Dict[str, Any]] = {}
    guardrails: Optional[Dict[str, Any]] = {}
    strategy: Optional[Dict[str, Any]] = {}
    rag_sources: Optional[Dict[str, Any]] = {}

class BrandUpdateRequest(BaseModel):
    brand_name: Optional[str] = None
    brand_type: Optional[str] = None
    product_nature: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    content_language: Optional[str] = None
    voice_profile: Optional[Dict[str, Any]] = None
    guardrails: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    rag_sources: Optional[Dict[str, Any]] = None

class VoiceSuggestionRequest(BaseModel):
    brand_type: str
    product_nature: str
    industry: str
    target_audience: str

class ToneSuggestionRequest(BaseModel):
    core_adjectives: List[str]

class LexiconSuggestionRequest(BaseModel):
    product_nature: str
    industry: str

class PostResponse(BaseModel):
    caption: str
    hashtags: list[str]
    full_caption: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    keyword: str
    image_prompt: str
    visual_style: str
    generation_method: str
    timestamp: str
    context_snippets: list[str] = []

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("index.html")

@app.get("/index.html")
async def redirect_index():
    """Redirect index.html to root"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)

@app.get("/styles.css")
async def get_styles():
    """Serve the CSS file"""
    return FileResponse("styles.css", media_type="text/css")

@app.get("/script.js")
async def get_script():
    """Serve the JavaScript file"""
    return FileResponse("script.js", media_type="application/javascript")

@app.get("/brand_onboarding.html")
async def get_brand_onboarding():
    """Serve the brand onboarding page"""
    return FileResponse("brand_onboarding.html")

@app.get("/brand_onboarding.css")
async def get_brand_onboarding_css():
    """Serve the brand onboarding CSS"""
    return FileResponse("brand_onboarding.css", media_type="text/css")

@app.get("/brand_onboarding.js")
async def get_brand_onboarding_js():
    """Serve the brand onboarding JavaScript"""
    return FileResponse("brand_onboarding.js", media_type="application/javascript")

@app.get("/brand_list.html")
async def get_brand_list():
    """Serve the brand list page"""
    return FileResponse("brand_list.html")

@app.get("/brand_list.css")
async def get_brand_list_css():
    """Serve the brand list CSS"""
    return FileResponse("brand_list.css", media_type="text/css")

@app.get("/brand_list.js")
async def get_brand_list_js():
    """Serve the brand list JavaScript"""
    return FileResponse("brand_list.js", media_type="application/javascript")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "caption_generator": "initialized",
        "image_generation": "Pollinations.ai (Free, No API Key Required)",
        "documents_loaded": len(caption_generator.documents)
    }

@app.post("/generate-post", response_model=PostResponse)
async def generate_post(request: PostRequest):
    """Generate complete social media post with caption, hashtags, and image"""
    try:
        platform = request.platform or 'instagram'
        logger.info(f"Generating post for keyword: {request.keyword}, brand_id: {request.brand_id}, platform: {platform}")
        
        # Load brand profile if specified
        if request.brand_id:
            caption_generator.load_brand_profile(request.brand_id)
        else:
            # Load active brand if no specific brand requested
            caption_generator.load_brand_profile()
        
        # Step 1: Generate complete post data with platform-specific requirements and scenario
        post_data = caption_generator.generate_complete_post(
            keyword=request.keyword, 
            platform=platform,
            scenario=request.scenario
        )
        
        logger.info(f"Generated caption: {post_data['caption'][:50]}...")
        logger.info(f"Image prompt: {post_data['image_prompt'][:100]}...")
        
        # Step 2: Generate image using Hugging Face API
        image_base64 = None
        try:
            image_base64 = await generate_image_with_hf(post_data['image_prompt'])
            logger.info("Image generated successfully with Hugging Face API")
        except Exception as e:
            logger.error(f"Error generating image with HF API: {e}")
            # Continue without image
        
        # Step 3: Return complete post with context snippets
        response = PostResponse(
            caption=post_data['caption'],
            hashtags=post_data['hashtags'],
            full_caption=post_data['full_caption'],
            image_base64=image_base64,
            keyword=post_data['keyword'],
            image_prompt=post_data['image_prompt'],
            visual_style=post_data['visual_style'],
            generation_method=post_data['generation_method'],
            timestamp=post_data['timestamp'],
            context_snippets=post_data.get('context_snippets', [])
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating post: {str(e)}")

async def generate_image_with_hf(prompt: str) -> str:
    """Generate image using Pollinations.ai - completely free, no API key needed"""
    try:
        logger.info(f"Generating image with Pollinations.ai for prompt: {prompt[:100]}...")
        
        # Coffee-focused quality enhancement
        enhanced_prompt = f"{prompt}, professional coffee photography, close-up coffee shot, artistic, photorealistic, highly detailed, natural lighting, warm tones, commercial quality"
        
        # Pollinations.ai uses a simple GET request with the prompt in the URL
        # No API key needed, completely free
        import urllib.parse
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # Pollinations.ai endpoint - returns image directly
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
        
        try:
            logger.info("Requesting image from Pollinations.ai...")
            response = requests.get(pollinations_url, timeout=1000)
            
            if response.status_code == 200:
                # Convert image bytes to base64
                image_bytes = response.content
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                logger.info(f"Image generated successfully with Pollinations.ai, size: {len(image_bytes)} bytes")
                return image_base64
            else:
                logger.error(f"Pollinations.ai error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Pollinations.ai request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Pollinations.ai request error: {e}")
            return None
        
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        return None

@app.post("/regenerate-image")
async def regenerate_image(request: dict):
    """Regenerate only the image and image prompt for current post with full RAG context"""
    try:
        keyword = request.get('keyword')
        caption = request.get('caption', '')
        context_snippets = request.get('context_snippets', [])
        
        logger.info(f"Regenerating image for keyword: {keyword}")
        logger.info(f"Using {len(context_snippets)} context snippets from original generation")
        
        # Create caption data structure for image prompt generation WITH context
        caption_data = {
            'keyword': keyword,
            'base_caption': caption,
            'context_snippets': context_snippets  # Use original RAG context
        }
        
        # Generate new image prompt with variation - this will use the same context
        # but add variation through randomization in the prompt generation
        new_image_prompt = caption_generator.generate_image_prompt(caption_data)
        logger.info(f"New image prompt generated: {new_image_prompt[:100]}...")
        
        # Generate new image with the new prompt
        image_base64 = None
        try:
            image_base64 = await generate_image_with_hf(new_image_prompt)
            logger.info("New image generated successfully with RAG context")
        except Exception as e:
            logger.error(f"Error generating new image: {e}")
        
        # Detect visual style from caption
        visual_style = caption_generator.detect_visual_style(caption)
        
        return {
            'image_prompt': new_image_prompt,
            'image_base64': image_base64,
            'visual_style': visual_style,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error regenerating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error regenerating image: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """Get generator statistics"""
    return {
        "total_documents": len(caption_generator.documents),
        "trending_keywords": len(caption_generator.trending_keywords),
        "hashtag_knowledge": len(getattr(caption_generator, 'hashtag_data', [])),
        "sources": {
            "coffee_articles": sum(1 for m in caption_generator.document_metadata if m.get('source') == 'coffee_articles'),
            "reddit": sum(1 for m in caption_generator.document_metadata if m.get('source') == 'reddit'),
            "twitter": sum(1 for m in caption_generator.document_metadata if m.get('source') == 'twitter'),
            "blogs": sum(1 for m in caption_generator.document_metadata if 'blog' in m.get('source', ''))
        },
        "llm_model": caption_generator.ollama_model if caption_generator.use_ollama else 'Local Fallback'
    }

# ========================================
# BRAND MANAGEMENT ENDPOINTS
# ========================================

@app.post("/api/brands/create")
async def create_brand(request: BrandCreateRequest):
    """Create a new brand profile"""
    try:
        brand_data = request.dict()
        result = brand_manager.create_brand(brand_data)
        return {
            "success": True,
            "message": f"Brand '{result['brand_name']}' created successfully",
            "brand": result
        }
    except Exception as e:
        logger.error(f"Error creating brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brands/list")
async def list_brands():
    """Get all brand profiles"""
    try:
        brands = brand_manager.get_all_brands()
        return {
            "success": True,
            "brands": brands,
            "total": len(brands)
        }
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brands/{brand_id}")
async def get_brand(brand_id: int):
    """Get a specific brand profile"""
    try:
        brand = brand_manager.get_brand(brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {
            "success": True,
            "brand": brand
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/brands/active/current")
async def get_active_brand():
    """Get the currently active brand"""
    try:
        brand = brand_manager.get_active_brand()
        if not brand:
            raise HTTPException(status_code=404, detail="No active brand found")
        return {
            "success": True,
            "brand": brand
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/brands/{brand_id}")
async def update_brand(brand_id: int, request: BrandUpdateRequest):
    """Update a brand profile"""
    try:
        brand_data = {k: v for k, v in request.dict().items() if v is not None}
        if not brand_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = brand_manager.update_brand(brand_id, brand_data)
        return {
            "success": True,
            "message": f"Brand updated successfully",
            "brand": result
        }
    except Exception as e:
        logger.error(f"Error updating brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/brands/{brand_id}/activate")
async def activate_brand(brand_id: int):
    """Set a brand as active"""
    try:
        result = brand_manager.set_active_brand(brand_id)
        return {
            "success": True,
            "message": f"Brand '{result['brand_name']}' is now active",
            "brand": result
        }
    except Exception as e:
        logger.error(f"Error activating brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/brands/{brand_id}")
async def delete_brand(brand_id: int):
    """Delete a brand profile"""
    try:
        deleted = brand_manager.delete_brand(brand_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Brand not found")
        return {
            "success": True,
            "message": "Brand deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting brand: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# LLM SUGGESTION ENDPOINTS
# ========================================

@app.post("/api/brands/suggest-voice")
async def suggest_voice_adjectives(request: VoiceSuggestionRequest):
    """Generate voice adjective suggestions using LLM"""
    try:
        brand_data = request.dict()
        suggestions = brand_manager.suggest_voice_adjectives(brand_data)
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error generating voice suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brands/suggest-tones")
async def suggest_tone_variations(request: ToneSuggestionRequest):
    """Generate tone variation table using LLM"""
    try:
        suggestions = brand_manager.suggest_tone_variations(request.core_adjectives)
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error generating tone suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/brands/suggest-lexicon")
async def suggest_lexicon(request: LexiconSuggestionRequest):
    """Generate lexicon suggestions (always use / never use)"""
    try:
        suggestions = brand_manager.suggest_lexicon(
            request.product_nature,
            request.industry
        )
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Error generating lexicon suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# PLATFORM ENDPOINTS
# ========================================

@app.get("/api/platforms/list")
async def list_platforms():
    """Get list of supported platforms"""
    try:
        platforms = platform_strategy.get_all_platforms()
        summaries = [platform_strategy.get_platform_summary(p) for p in platforms]
        return {
            "success": True,
            "platforms": summaries
        }
    except Exception as e:
        logger.error(f"Error listing platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/platforms/{platform}/spec")
async def get_platform_spec(platform: str):
    """Get specifications for a specific platform"""
    try:
        summary = platform_strategy.get_platform_summary(platform)
        return {
            "success": True,
            "platform_spec": summary
        }
    except Exception as e:
        logger.error(f"Error getting platform spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
