"""
HuggingFace Gateway Module
Handles all HuggingFace Inference API calls for AI/NLP tasks.
Supports mock mode when HF_API_TOKEN is not configured.
"""

from typing import Dict, List
from .base_gateway import BaseGateway


class HFGateway(BaseGateway):
    """
    Gateway for HuggingFace Inference API integration.
    
    Responsibilities:
    - Analyze text using HuggingFace models (sentiment analysis)
    - Return mock analysis when API token is not configured
    
    Mock Mode:
    - Activated when HF_API_TOKEN is missing
    - Returns fake sentiment analysis for testing
    """
    
    def _get_required_config_keys(self) -> list[str]:
        """Required configuration keys for HuggingFace API"""
        return ["HF_API_TOKEN"]
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    async def analyze_text(self, text: str) -> Dict:
        """
        Analyze text for sentiment and extract keywords.
        
        Args:
            text: Text to analyze (travel-related content)
        
        Returns:
            Analysis result with sentiment, confidence, keywords
        
        Mock Mode:
            Returns fake sentiment analysis based on simple keyword detection
        """
        if self.is_mock_mode():
            return await self._mock_analyze_text(text)
        
        # Real API call
        return await self._real_analyze_text(text)
    
    # ========================================================================
    # Mock Mode Implementation
    # ========================================================================
    
    async def _mock_analyze_text(self, text: str) -> Dict:
        """
        Generate mock sentiment analysis.
        Uses simple keyword detection for realistic results.
        """
        text_lower = text.lower()
        
        # Positive keywords
        positive_keywords = [
            "love", "amazing", "beautiful", "wonderful", "great", "excellent",
            "fantastic", "paradise", "dream", "perfect", "relaxing", "peaceful"
        ]
        
        # Negative keywords
        negative_keywords = [
            "bad", "terrible", "awful", "horrible", "disappointing", "worst",
            "crowded", "expensive", "dirty", "dangerous"
        ]
        
        # Travel-related keywords
        travel_keywords = [
            "beach", "mountain", "city", "hotel", "flight", "vacation",
            "trip", "destination", "travel", "adventure", "explore", "visit",
            "culture", "food", "nature", "relax", "warm", "cold"
        ]
        
        # Count keyword matches
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        # Determine sentiment
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = min(0.95, 0.65 + (positive_count * 0.1))
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = min(0.95, 0.65 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.60
        
        # Extract travel keywords found in text
        found_keywords = [kw for kw in travel_keywords if kw in text_lower]
        
        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "keywords": found_keywords[:5],  # Limit to 5 keywords
            "mock": True
        }
    
    # ========================================================================
    # Real API Implementation
    # ========================================================================
    
    async def _real_analyze_text(self, text: str) -> Dict:
        """
        Real HuggingFace API implementation for sentiment analysis.
        Uses distilbert-base-uncased-finetuned-sst-2-english model.
        """
        model = "distilbert-base-uncased-finetuned-sst-2-english"
        url = f"https://api-inference.huggingface.co/models/{model}"
        
        headers = {
            "Authorization": f"Bearer {self._get_config('HF_API_TOKEN')}"
        }
        
        payload = {
            "inputs": text
        }
        
        try:
            # Make request with retry logic
            response = await self._retry_request(
                lambda: self._make_request("POST", url, json=payload, headers=headers)
            )
            
            # Parse HuggingFace response
            # Response format: [[{"label": "POSITIVE", "score": 0.999}]]
            if response and len(response) > 0 and len(response[0]) > 0:
                result = response[0][0]
                sentiment = result["label"].lower()
                confidence = result["score"]
                
                # Extract keywords (simple approach)
                keywords = self._extract_keywords(text)
                
                return {
                    "sentiment": sentiment,
                    "confidence": round(confidence, 2),
                    "keywords": keywords,
                    "mock": False
                }
            else:
                self.logger.warning("Unexpected HuggingFace response format, using mock")
                return await self._mock_analyze_text(text)
        
        except Exception as e:
            self.logger.error(f"HuggingFace API error: {e}, falling back to mock")
            return await self._mock_analyze_text(text)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Simple keyword extraction from text.
        In production, use a proper NLP library or HuggingFace model.
        """
        # Common travel keywords
        travel_keywords = [
            "beach", "mountain", "city", "hotel", "flight", "vacation",
            "trip", "destination", "travel", "adventure", "explore", "visit",
            "culture", "food", "nature", "relax", "warm", "cold", "sunny",
            "tropical", "historic", "modern", "quiet", "peaceful"
        ]
        
        text_lower = text.lower()
        found = [kw for kw in travel_keywords if kw in text_lower]
        
        return found[:5]  # Limit to 5 keywords
