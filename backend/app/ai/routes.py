"""
AI Router Module
HTTP endpoints for AI-related operations (text analysis, NLP, LLM consultation).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List
import logging

from app.gateway import HFGateway
from app.services import AIService
from app.ai.schemas import ConsultRequest, ConsultResponse
from app.ai.provider_factory import get_llm_provider


logger = logging.getLogger(__name__)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ============================================================================
# Dependency Injection (with proper cleanup)
# ============================================================================

async def get_ai_service():
    """
    Dependency factory for AIService (HuggingFace).
    Creates gateway and service instances with proper cleanup.
    """
    async with HFGateway() as gateway:
        # For old analyze endpoint - requires HF gateway
        yield AIService(llm_provider=None, hf_gateway=gateway)


async def get_llm_ai_service():
    """
    Dependency factory for AIService with LLM provider.
    Gère le lifecycle du provider (fermeture propre du httpx client).
    """
    provider = get_llm_provider()  # Factory selon LLM_PROVIDER env
    
    # Gestion lifecycle: utiliser context manager si disponible
    if hasattr(provider, "__aenter__"):
        # Provider supporte async context manager (BaseGateway)
        async with provider as p:
            yield AIService(llm_provider=p, hf_gateway=None)
    else:
        # Fallback: appel close() manuellement
        try:
            yield AIService(llm_provider=provider, hf_gateway=None)
        finally:
            if hasattr(provider, "close"):
                await provider.close()


# ============================================================================
# Request/Response Models (Old analyze endpoint)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Request model for text analysis"""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Text to analyze (10-500 characters)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "text": "I want to visit a warm beach destination for relaxation and enjoy the sun"
            }]
        }
    }


class AnalyzeResponse(BaseModel):
    """Response model for text analysis"""
    sentiment: str = Field(..., description="Sentiment: positive, neutral, or negative")
    confidence: float = Field(..., description="Confidence score (0-1)")
    keywords: List[str] = Field(..., description="Extracted travel keywords")
    travel_intent: str = Field(..., description="Interpreted travel intent category")
    mock: bool = Field(default=False, description="True if using mock data")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "sentiment": "positive",
                "confidence": 0.92,
                "keywords": ["beach", "warm", "relax", "sun"],
                "travel_intent": "enthusiastic_traveler_seeking_relaxation",
                "mock": True
            }]
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


@router.post("/consult", response_model=ConsultResponse)
async def consult(
    request: ConsultRequest,
    service: AIService = Depends(get_llm_ai_service)
):
    """
    Consulter l'assistant IA pour aide à la décision voyage.
    
    **Modes disponibles**:
    - **compare**: Comparer 2+ offres (context.selected_offers requis, ≥2 offres)
    - **budget**: Conseils selon budget (context.budget_max requis)
    - **policy**: Expliquer une politique (message contient le texte)
    - **free**: Question libre
    
    **Réponse inclut toujours**:
    - answer: Texte de réponse du LLM
    - model: Nom du modèle utilisé (ex: "qwen2.5:3b" ou "mock-ollama")
    - meta.mock: bool indiquant si mode démo (Ollama indisponible)
    - meta.reason: Explication si mode mock (ex: "ollama_unreachable")
    
    **Configuration**:
    - Nécessite Ollama en cours d'exécution: `ollama serve`
    - Modèle requis: `ollama pull qwen2.5:3b`
    - Variables env: OLLAMA_BASE_URL, OLLAMA_MODEL
    """
    try:
        # Convert ConsultContext to dict for service
        context_dict = request.context.model_dump()
        
        result = await service.consult(
            mode=request.mode,
            message=request.message,
            context=context_dict,
            language=request.language
        )
        return result
    except ValueError as e:
        # Validation errors (prompt too long, missing required context fields)
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Consultation failed")
        raise HTTPException(status_code=500, detail=f"Consultation failed: {str(e)}")

