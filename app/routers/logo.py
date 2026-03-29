"""
Logo Generator Router
API endpoint for generating logos using Stability AI SDXL.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.models import LogoPromptRequest, LogoPromptResponse, ErrorResponse
from app.config import get_settings
import base64
import httpx

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("bizforge.logo")


@router.post(
    "/logo/prompt",
    response_model=LogoPromptResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Generate Logo",
    description="Generate a logo image using Stability AI SDXL."
)
async def generate_logo_prompt(request: LogoPromptRequest):
    """
    Generate logo design using Stability AI SDXL.
    """
    try:
        # Construct optimized logo prompt
        image_prompt = f"{request.style} logo for {request.brand_name}, {request.industry}, vector art, minimal, clean white background, high quality, professional design, centered"
        
        image_url = ""
        model_used = "unknown"
        
        # Primary: Stability AI SDXL (requires STABILITY_API_KEY)
        if settings.stability_api_key:
            try:
                stability_api_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {settings.stability_api_key}",
                }
                payload = {
                    "text_prompts": [
                        {"text": image_prompt, "weight": 1},
                        {"text": "blurry, low quality, distorted, text", "weight": -1}  # Negative prompt
                    ],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "samples": 1,
                    "steps": 30,
                    "style_preset": "digital-art"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(stability_api_url, headers=headers, json=payload, timeout=60.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        base64_image = data["artifacts"][0]["base64"]
                        image_url = f"data:image/png;base64,{base64_image}"
                        model_used = "Stability AI SDXL"
                        logger.info("Successfully generated logo using Stability AI")
                    else:
                        error_text = response.text[:300] if response.text else "Unknown error"
                        logger.warning(f"Stability AI Error {response.status_code}: {error_text}")
            except Exception as e:
                logger.error(f"Stability AI request failed: {e}")
        
        # Fallback: Placeholder if Stability AI fails or not configured
        if not image_url:
            image_url = "https://via.placeholder.com/512x512.png?text=Logo+Generation+Failed"
            model_used = "Placeholder"
        
        return LogoPromptResponse(
            success=True,
            prompts=None,
            image_url=image_url,
            model_used=model_used
        )
    except Exception as e:
        logger.error(f"Logo generator endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Logo generation failed: {str(e)}"
        )
