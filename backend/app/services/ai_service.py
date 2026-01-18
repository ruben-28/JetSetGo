"""
AI Service Module
Business logic for AI-related operations (text analysis, NLP) and LLM consultation.
"""

import os
from typing import Dict, Optional, Any
from fastapi import HTTPException
from app.gateway import HFGateway, LLMProvider
from app.services.prompt_templates import PromptTemplates


class AIService:
    """
    Service layer for AI operations.
    
    Responsibilities:
    - Implement business logic for text analysis (HuggingFace)
    - Implement business logic for LLM consultation (Ollama/OpenAI)
    - Validate text inputs
    - Orchestrate gateway calls
    - Build prompts from templates
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,  # REQUIRED for consult()
        hf_gateway: Optional[HFGateway] = None  # Optional (for analyze_travel_intent)
    ):
        """
        Initialize service with dependencies.
        
        Args:
            llm_provider: LLM provider instance (Ollama, OpenAI, etc.) - REQUIRED
            hf_gateway: HuggingFace gateway instance - Optional
        """
        self.llm_provider = llm_provider
        self.hf_gateway = hf_gateway
    
    # ========================================================================
    # LLM Consultation Methods (NEW)
    # ========================================================================
    
    async def consult(
        self,
        mode: str,
        message: str,
        context: Dict[str, Any],
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Consult LLM for travel decision assistance.
        
        Args:
            mode: Consultation mode (compare, budget, policy, free)
            message: User's message/question
            context: Typed context dict (from ConsultContext)
            language: Response language (default: fr)
        
        Returns:
            Dict with keys: answer, model, tokens_estimate, sources, meta
        
        Raises:
            ValueError: On validation errors
            HTTPException: On service errors
        """
        # 1. Validate prompt length
        self._validate_prompt(message)
        
        # 2. Build prompts from templates
        system_prompt = PromptTemplates.get_system_prompt(mode)
        user_prompt = PromptTemplates.build_user_prompt(mode, message, context)
        
        # 3. Call LLM provider
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
                detail=f"LLM request failed: {str(e)}"
            )
        
        # 4. Return with model and meta ALWAYS present
        return {
            "answer": result["content"],
            "model": result.get("model", "unknown"),
            "tokens_estimate": result.get("tokens"),
            "sources": [],  # Future RAG
            "meta": result.get("meta", {"mock": False})
        }
    
    def _validate_prompt(self, message: str):
        """
        Validate prompt length.
        
        Args:
            message: User message to validate
        
        Raises:
            ValueError: If message exceeds MAX_PROMPT_CHARS
        """
        max_chars = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
        if len(message) > max_chars:
            raise ValueError(f"Message too long ({len(message)} chars, max {max_chars})")
    
    # ========================================================================
    # Existing Methods (HuggingFace - unchanged)
    # ========================================================================
    
    async def analyze_travel_intent(self, text: str) -> Dict:
        """
        Analyze user text for travel intent and sentiment.
        
        Note: Requires hf_gateway to be set. This is the OLD method.
        
        Args:
            text: User input text (travel-related)
        
        Returns:
            Analysis result with sentiment, confidence, keywords, travel_intent
        
        Raises:
            HTTPException: On validation errors
        """
        if not self.hf_gateway:
            raise HTTPException(
                status_code=500,
                detail="HuggingFace gateway not configured for this service instance"
            )
        
        # 1. Validate input
        self._validate_text(text)
        
        # 2. Call gateway for sentiment analysis
        analysis = await self.hf_gateway.analyze_text(text)
        
        # 3. Add travel-specific interpretation
        travel_intent = self._interpret_travel_intent(
            analysis["sentiment"],
            analysis["keywords"]
        )
        
        # 4. Return enriched result
        return {
            "sentiment": analysis["sentiment"],
            "confidence": analysis["confidence"],
            "keywords": analysis["keywords"],
            "travel_intent": travel_intent,
            "mock": analysis.get("mock", False)
        }
    
    # ========================================================================
    # Business Logic & Validation (HuggingFace - unchanged)
    # ========================================================================
    
    def _validate_text(self, text: str):
        """
        Validate text input for HF analysis.
        
        Rules:
        - Text must be between 10 and 500 characters
        - Text must not be empty or only whitespace
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        text_length = len(text.strip())
        
        if text_length < 10:
            raise HTTPException(
                status_code=400,
                detail="Text must be at least 10 characters long"
            )
        
        if text_length > 500:
            raise HTTPException(
                status_code=400,
                detail="Text must not exceed 500 characters"
            )
    
    def _interpret_travel_intent(self, sentiment: str, keywords: list) -> str:
        """
        Interpret sentiment and keywords for travel context.
        
        Maps sentiment to travel intent categories:
        - positive → "enthusiastic_traveler"
        - neutral → "curious_explorer"
        - negative → "concerned_traveler"
        
        Args:
            sentiment: Sentiment from AI analysis
            keywords: Extracted keywords
        
        Returns:
            Travel intent category
        """
        # Map sentiment to travel intent
        intent_map = {
            "positive": "enthusiastic_traveler",
            "neutral": "curious_explorer",
            "negative": "concerned_traveler"
        }
        
        base_intent = intent_map.get(sentiment, "curious_explorer")
        
        # Refine based on keywords
        if any(kw in keywords for kw in ["beach", "relax", "peaceful", "warm"]):
            return f"{base_intent}_seeking_relaxation"
        elif any(kw in keywords for kw in ["adventure", "explore", "mountain", "nature"]):
            return f"{base_intent}_seeking_adventure"
        elif any(kw in keywords for kw in ["city", "culture", "food", "historic"]):
            return f"{base_intent}_seeking_culture"
        
        return base_intent
