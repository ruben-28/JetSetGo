"""
AI Service Module
Business logic for AI-related operations (text analysis, NLP).
"""

from typing import Dict
from fastapi import HTTPException
from app.gateway import HFGateway


class AIService:
    """
    Service layer for AI operations.
    
    Responsibilities:
    - Implement business logic for text analysis
    - Validate text inputs
    - Interpret AI results for travel context
    - Orchestrate HuggingFace gateway calls
    """
    
    def __init__(self, gateway: HFGateway):
        """
        Initialize service with gateway dependency.
        
        Args:
            gateway: HFGateway instance for HuggingFace API calls
        """
        self.gateway = gateway
    
    # ========================================================================
    # Public Service Methods
    # ========================================================================
    
    async def analyze_travel_intent(self, text: str) -> Dict:
        """
        Analyze user text for travel intent and sentiment.
        
        Args:
            text: User input text (travel-related)
        
        Returns:
            Analysis result with sentiment, confidence, keywords, travel_intent
        
        Raises:
            HTTPException: On validation errors
        """
        # 1. Validate input
        self._validate_text(text)
        
        # 2. Call gateway for sentiment analysis
        analysis = await self.gateway.analyze_text(text)
        
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
    # Business Logic & Validation
    # ========================================================================
    
    def _validate_text(self, text: str):
        """
        Validate text input.
        
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
