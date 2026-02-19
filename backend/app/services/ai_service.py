"""
Fichier: backend/app/services/ai_service.py
Objectif: Logique métier pour les opérations liées à l'IA (analyse de texte, NLP) et consultation de LLM.
"""

import os
from typing import Dict, Optional, Any
from fastapi import HTTPException
from app.gateway import HFGateway, LLMProvider
from app.services.prompt_templates import PromptTemplates


class AIService:
    """
    Couche de service pour les opérations d'IA.
    
    Responsabilités:
    - Implémenter la logique d'analyse de texte (HuggingFace).
    - Implémenter la logique de consultation LLM (Ollama/OpenAI).
    - Valider les entrées textuelles.
    - Orchestrer les appels aux gateways.
    - Construire les prompts à partir des templates.
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,  # REQUIS pour consult()
        hf_gateway: Optional[HFGateway] = None  # Optionnel (pour analyze_travel_intent)
    ):
        """
        Initialise le service avec les dépendances.
        
        Args:
            llm_provider: Instance du provider LLM (Ollama, OpenAI, etc.) - REQUIS
            hf_gateway: Instance du gateway HuggingFace - Optionnel
        """
        self.llm_provider = llm_provider
        self.hf_gateway = hf_gateway
    
    # ========================================================================
    # Méthodes de Consultation LLM (NOUVEAU)
    # ========================================================================
    
    async def consult(
        self,
        mode: str,
        message: str,
        context: Dict[str, Any],
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Consulter le LLM pour une assistance au voyage.
        
        Args:
            mode: Mode de consultation (compare, budget, policy, free)
            message: Message/Question de l'utilisateur
            context: Dictionnaire de contexte typé (depuis ConsultContext)
            language: Langue de réponse (défaut: fr)
        
        Returns:
            Dict avec clés: answer, model, tokens_estimate, sources, meta
        
        Raises:
            ValueError: En cas d'erreur de validation
            HTTPException: En cas d'erreur du service
        """
        # 1. Valider la longueur du prompt
        self._validate_prompt(message)
        
        # 2. Construire les prompts depuis les templates
        system_prompt = PromptTemplates.get_system_prompt(mode)
        user_prompt = PromptTemplates.build_user_prompt(mode, message, context)
        
        # 3. Appeler le provider LLM
        try:
            result = await self.llm_provider.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Échec requête LLM : {str(e)}"
            )
        
        # 4. Retourner avec modèle et méta TOUJOURS présents
        return {
            "answer": result["content"],
            "model": result.get("model", "unknown"),
            "tokens_estimate": result.get("tokens"),
            "sources": [],  # Futur RAG
            "meta": result.get("meta", {"mock": False})
        }
    
    def _validate_prompt(self, message: str):
        """
        Valider la longueur du prompt.
        
        Args:
            message: Message utilisateur à valider
        
        Raises:
            ValueError: Si le message dépasse MAX_PROMPT_CHARS
        """
        max_chars = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
        if len(message) > max_chars:
            raise ValueError(f"Message trop long ({len(message)} chars, max {max_chars})")
    
    # ========================================================================
    # Méthodes Existantes (HuggingFace - inchangé)
    # ========================================================================
    
    async def analyze_travel_intent(self, text: str) -> Dict:
        """
        Analyser le texte utilisateur pour l'intention de voyage et le sentiment.
        
        Note: Nécessite hf_gateway configuré. (Méthode ANCIENNE)
        
        Args:
            text: Texte d'entrée utilisateur
        
        Returns:
            Résultat d'analyse avec sentiment, confiance, mots-clés, intention voyage
        
        Raises:
            HTTPException: En cas d'erreur de validation
        """
        if not self.hf_gateway:
            raise HTTPException(
                status_code=500,
                detail="Gateway HuggingFace non configurée pour cette instance de service"
            )
        
        # 1. Valider l'entrée
        self._validate_text(text)
        
        # 2. Appeler le gateway pour l'analyse de sentiment
        analysis = await self.hf_gateway.analyze_text(text)
        
        # 3. Ajouter l'interprétation spécifique voyage
        travel_intent = self._interpret_travel_intent(
            analysis["sentiment"],
            analysis["keywords"]
        )
        
        # 4. Retourner le résultat enrichi
        return {
            "sentiment": analysis["sentiment"],
            "confidence": analysis["confidence"],
            "keywords": analysis["keywords"],
            "travel_intent": travel_intent,
            "mock": analysis.get("mock", False)
        }
    
    # ========================================================================
    # Logique Métier & Validation (HuggingFace - inchangé)
    # ========================================================================
    
    def _validate_text(self, text: str):
        """
        Valider le texte pour l'analyse HF.
        
        Règles:
        - Le texte doit faire entre 10 et 500 caractères.
        - Le texte ne doit pas être vide.
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Le texte ne peut pas être vide"
            )
        
        text_length = len(text.strip())
        
        if text_length < 10:
            raise HTTPException(
                status_code=400,
                detail="Le texte doit contenir au moins 10 caractères"
            )
        
        if text_length > 500:
            raise HTTPException(
                status_code=400,
                detail="Le texte ne doit pas dépasser 500 caractères"
            )
    
    def _interpret_travel_intent(self, sentiment: str, keywords: list) -> str:
        """
        Interpréter le sentiment et les mots-clés dans un contexte voyage.
        
        Mappe le sentiment vers des catégories d'intention :
        - positive → "enthusiastic_traveler"
        - neutral → "curious_explorer"
        - negative → "concerned_traveler"
        
        Args:
            sentiment: Sentiment de l'analyse IA
            keywords: Mots-clés extraits
        
        Returns:
            Catégorie d'intention voyage
        """
        # Map sentiment vers intention voyage
        intent_map = {
            "positive": "enthusiastic_traveler",
            "neutral": "curious_explorer",
            "negative": "concerned_traveler"
        }
        
        base_intent = intent_map.get(sentiment, "curious_explorer")
        
        # Affiner avec les mots-clés
        if any(kw in keywords for kw in ["beach", "relax", "peaceful", "warm"]):
            return f"{base_intent}_seeking_relaxation"
        elif any(kw in keywords for kw in ["adventure", "explore", "mountain", "nature"]):
            return f"{base_intent}_seeking_adventure"
        elif any(kw in keywords for kw in ["city", "culture", "food", "historic"]):
            return f"{base_intent}_seeking_culture"
        
        return base_intent
