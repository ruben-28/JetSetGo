"""
Module Routeur AI
Endpoints HTTP pour les opérations liées à l'IA (analyse de texte, NLP, consultation LLM, assistant).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.gateway import HuggingFaceGateway
from app.services import AIService
from app.ai.schemas import ConsultRequest, ConsultResponse
from app.ai.provider_factory import get_llm_provider
from app.ai.assistant_orchestrator import AssistantOrchestrator
from app.auth.dependencies import get_current_user
from app.auth.models import User


logger = logging.getLogger(__name__)


# ============================================================================
# Configuration du Routeur
# ============================================================================

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ============================================================================
# Injection de Dépendances (avec nettoyage approprié)
# ============================================================================

async def get_ai_service():
    """
    Factory de dépendance pour AIService (HuggingFace).
    Crée les instances gateway et service avec un nettoyage approprié.
    """
    async with HuggingFaceGateway() as gateway:
        # Pour l'ancien endpoint analyze - nécessite le gateway HF
        yield AIService(llm_provider=None, hf_gateway=gateway)


async def get_llm_ai_service():
    """
    Factory de dépendance pour AIService avec provider LLM.
    Gère le cycle de vie du provider (fermeture propre du client httpx).
    """
    provider = get_llm_provider()  # Factory selon env LLM_PROVIDER
    
    # Gestion lifecycle : utiliser context manager si disponible
    if hasattr(provider, "__aenter__"):
        # Le Provider supporte async context manager (BaseGateway)
        async with provider as p:
            yield AIService(llm_provider=p, hf_gateway=None)
    else:
        # Fallback : appel close() manuellement
        try:
            yield AIService(llm_provider=provider, hf_gateway=None)
        finally:
            if hasattr(provider, "close"):
                await provider.close()


# ============================================================================
# Modèles Requête/Réponse (Ancien endpoint analyze)
# ============================================================================

class AnalyzeRequest(BaseModel):
    """Modèle de requête pour l'analyse de texte"""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Texte à analyser (10-500 caractères)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "text": "Je veux visiter une destination plage chaude et me détendre au soleil"
            }]
        }
    }


class AnalyzeResponse(BaseModel):
    """Modèle de réponse pour l'analyse de texte"""
    sentiment: str = Field(..., description="Sentiment : positif, neutre ou négatif")
    confidence: float = Field(..., description="Score de confiance (0-1)")
    keywords: List[str] = Field(..., description="Mots-clés de voyage extraits")
    travel_intent: str = Field(..., description="Catégorie d'intention de voyage interprétée")
    mock: bool = Field(default=False, description="Vrai si des données factices sont utilisées")
    
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
# Modèles Requête/Réponse Assistant (NOUVEAU)
# ============================================================================

class AssistantRequest(BaseModel):
    """Requête pour l'assistant IA."""
    message: str = Field(..., min_length=1, max_length=500, description="Message de l'utilisateur")


class AssistantResponse(BaseModel):
    """Réponse de l'assistant IA."""
    action: str = Field(..., description="Type d'action : navigate, prefill_search, display_results, chat_only")
    target_view: Optional[str] = Field(None, description="Vue cible : flights, hotels, packages, null")
    prefill_data: Optional[Dict[str, Any]] = Field(None, description="Données à pré-remplir dans le formulaire")
    search_results: Optional[List[Dict]] = Field(None, description="Résultats de recherche si action est display_results")
    response_text: str = Field(..., description="Réponse en langage naturel à afficher")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées supplémentaires")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    service: AIService = Depends(get_ai_service)
):
    """
    Analyser un texte lié au voyage pour le sentiment et l'intention.
    
    **Cas d'usage**: Analyser l'entrée utilisateur pour comprendre ses préférences et son humeur.
    
    Corps de requête :
    - text: Texte d'entrée utilisateur (10-500 caractères)
    
    Retourne :
    - sentiment: Sentiment détecté (positif, neutre, négatif)
    - confidence: Score de confiance (0-1)
    - keywords: Mots-clés extraits
    - travel_intent: Catégorie d'intention de voyage interprétée
    - mock: Si des données mock ont été utilisées (Vrai si HF_API_TOKEN non configuré)
    
    Exemples :
    - "Je veux aller au soleil" → positive, seeking_relaxation
    """
    try:
        result = await service.analyze_travel_intent(request.text)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"L'analyse a échoué : {str(e)}")


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
        # Convertir ConsultContext en dict pour le service
        context_dict = request.context.model_dump()
        
        result = await service.consult(
            mode=request.mode,
            message=request.message,
            context=context_dict,
            language=request.language
        )
        return result
    except ValueError as e:
        # Erreurs de validation (prompt trop long, champs requis manquants)
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("La consultation a échoué")
        raise HTTPException(status_code=500, detail=f"La consultation a échoué : {str(e)}")


@router.post("/assistant", response_model=AssistantResponse)
async def query_assistant(
    request: AssistantRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint principal de l'assistant IA utilisant l'architecture HuggingFace + Ollama.
    
    Traite le message utilisateur via :
    1. Analyse Hugging Face (classification d'intention + extraction d'entités)
    2. Orchestration Backend (logique de décision)
    3. Génération Ollama (réponse en langage naturel)
    
    **Actions**:
    - **navigate**: Naviguer vers une vue spécifique avec données pré-remplies
    - **display_results**: Afficher les résultats de recherche dans la vue cible
    - **chat_only**: Afficher juste le texte de réponse (pas de navigation)
    
    **Exemple**:
    Utilisateur : "Je cherche un vol pour Paris"
    →
    {
      "action": "navigate",
      "target_view": "flights",
      "prefill_data": {"destination": "Paris"},
      "response_text": "Je vous amène à la recherche de vols pour Paris."
    }
    """
    orchestrator = AssistantOrchestrator()
    
    try:
        result = await orchestrator.process_message(
            user_message=request.message,
            user_id=current_user.id
        )
        return result
    
    except Exception as e:
        logger.exception("Erreur assistant")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur assistant : {str(e)}"
        )

