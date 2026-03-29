"""
Brand Name Generator Router
API endpoint for generating creative brand names.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.models import BrandNameRequest, BrandNameResponse, ErrorResponse
from app.services.ai_service import get_ai_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("bizforge.brand")


@router.post(
    "/brand/generate-name",
    response_model=BrandNameResponse,
    responses={500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Generate Brand Names",
    description="Generate creative, memorable brand name suggestions based on industry, keywords, and style preferences."
)
async def generate_brand_name(request: BrandNameRequest):
    """
    Generate brand name suggestions using AI.
    
    - **industry**: The industry or niche for the brand
    - **keywords**: Keywords or themes to incorporate
    - **style**: Naming style (modern, classic, playful, etc.)
    - **target_audience**: Description of target audience
    - **context**: Additional context or requirements
    """
    try:
        ai_service = get_ai_service()
        suggestions = ai_service.generate_brand_names(
            industry=request.industry,
            keywords=request.keywords,
            style=request.style,
            target_audience=request.target_audience,
            context=request.context
        )
        
        return BrandNameResponse(
            success=True,
            suggestions=suggestions,
            model_used=settings.model_name
        )
    except ValueError as e:
        logger.warning(f"AI service not configured: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Brand name generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate brand names: {str(e)}"
        )
