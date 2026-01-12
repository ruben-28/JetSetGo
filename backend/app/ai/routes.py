"""
AI Router Module
HTTP endpoints for AI-related operations (text analysis, NLP).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List

from app.gateway import HFGateway
from app.services import AIService


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ============================================================================
# Dependency Injection (with proper cleanup)
# ============================================================================

async def get_ai_service():
    """
    Dependency factory for AIService.
    Creates gateway and service instances with proper cleanup.
    """
    async with HFGateway() as gateway:
        yield AIService(gateway)



# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Text to analyze (10-500 characters)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "I want to visit a warm beach destination for relaxation and enjoy the sun"
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for text analysis"""
    sentiment: str = Field(..., description="Sentiment: positive, neutral, or negative")
    confidence: float = Field(..., description="Confidence score (0-1)")
    keywords: List[str] = Field(..., description="Extracted travel keywords")
    travel_intent: str = Field(..., description="Interpreted travel intent category")
    mock: bool = Field(default=False, description="True if using mock data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sentiment": "positive",
                "confidence": 0.92,
                "keywords": ["beach", "warm", "relax", "sun"],
                "travel_intent": "enthusiastic_traveler_seeking_relaxation",
                "mock": True
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    service: AIService = Depends(get_ai_service)
):
    """
    Analyze travel-related text for sentiment and intent.
    
    **Use Case**: Analyze user input to understand their travel preferences and mood.
    
    Request Body:
    - text: User input text (10-500 characters)
    
    Returns:
    - sentiment: Detected sentiment (positive, neutral, negative)
    - confidence: Confidence score (0-1)
    - keywords: Extracted travel-related keywords
    - travel_intent: Interpreted travel intent category
    - mock: Whether mock data was used (True if HF_API_TOKEN not configured)
    
    Examples:
    - "I want to visit a warm beach destination" → positive, seeking_relaxation
    - "Looking for adventure in the mountains" → positive, seeking_adventure
    - "Interested in exploring historic cities" → neutral, seeking_culture
    """
    try:
        result = await service.analyze_travel_intent(request.text)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
