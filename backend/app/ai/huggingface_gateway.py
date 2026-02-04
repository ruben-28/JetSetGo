"""
Hugging Face Gateway - Analysis Layer

Responsibilities:
- Intent classification
- Entity extraction (cities, dates, budget, preferences)
- Return structured JSON

Uses lightweight models for fast local inference.
"""
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid loading models at startup
_intent_classifier = None
_entity_extractor = None


def _get_intent_classifier():
    """Lazy load intent classifier."""
    global _intent_classifier
    if _intent_classifier is None:
        try:
            from transformers import pipeline
            _intent_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            logger.info("Intent classifier loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load intent classifier: {e}")
            _intent_classifier = False  # Mark as failed
    return _intent_classifier if _intent_classifier != False else None


def _get_entity_extractor():
    """Lazy load entity extractor."""
    global _entity_extractor
    if _entity_extractor is None:
        try:
            from transformers import pipeline
            _entity_extractor = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple"
            )
            logger.info("Entity extractor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load entity extractor: {e}")
            _entity_extractor = False
    return _entity_extractor if _entity_extractor != False else None


class HuggingFaceGateway:
    """Analysis layer using Hugging Face models."""
    
    def __init__(self):
        """Initialize gateway (models loaded lazily on first use)."""
        pass
    
    def analyze_message(self, user_message: str) -> Dict:
        """
        Main entry point: analyze user message and return structured JSON.
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "entities": {...},
                "raw_message": str
            }
        """
        try:
            # 1. Classify intent
            intent_result = self._classify_intent(user_message)
            
            # 2. Extract entities
            entities = self._extract_entities(user_message)
            
            return {
                "intent": intent_result["label"],
                "confidence": intent_result["score"],
                "entities": entities,
                "raw_message": user_message
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Fallback to simple keyword matching
            return self._fallback_analysis(user_message)
    
    def _classify_intent(self, message: str) -> Dict:
        """Classify user intent into predefined categories."""
        classifier = _get_intent_classifier()
        
        if classifier is None:
            # Fallback to keyword matching
            return self._keyword_intent(message)
        
        try:
            candidate_labels = [
                "flight_search",
                "hotel_search",
                "package_search",
                "inspiration",
                "booking_question",
                "price_inquiry"
            ]
            
            result = classifier(
                message,
                candidate_labels,
                multi_label=False
            )
            
            return {
                "label": result["labels"][0],
                "score": result["scores"][0]
            }
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return self._keyword_intent(message)
    
    def _keyword_intent(self, message: str) -> Dict:
        """Fallback intent detection using keywords."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["vol", "flight", "avion", "fly"]):
            return {"label": "flight_search", "score": 0.8}
        elif any(word in message_lower for word in ["hotel", "hôtel", "hébergement", "accommodation"]):
            return {"label": "hotel_search", "score": 0.8}
        elif any(word in message_lower for word in ["package", "voyage", "séjour", "trip"]):
            return {"label": "package_search", "score": 0.8}
        elif any(word in message_lower for word in ["idée", "inspiration", "suggest", "recommand"]):
            return {"label": "inspiration", "score": 0.7}
        else:
            return {"label": "general", "score": 0.5}
    
    def _extract_entities(self, message: str) -> Dict:
        """Extract structured entities from message."""
        extractor = _get_entity_extractor()
        
        locations = []
        if extractor:
            try:
                ner_results = extractor(message)
                locations = [
                    entity["word"] for entity in ner_results 
                    if entity["entity_group"] == "LOC"
                ]
            except Exception as e:
                logger.warning(f"NER extraction failed: {e}")
        
        # Always try regex-based extraction
        dates = self._extract_dates(message)
        travelers = self._extract_travelers(message)
        budget_level = self._classify_budget(message)
        preferences = self._extract_preferences(message)
        
        return {
            "destination": locations[0] if locations else self._extract_city_keywords(message),
            "dates": dates,
            "travelers": travelers,
            "budget_level": budget_level,
            "preferences": preferences
        }
    
    def _extract_city_keywords(self, message: str) -> Optional[str]:
        """Extract city names using keyword matching."""
        cities = [
            "Paris", "London", "New York", "Tokyo", "Rome", "Barcelona",
            "Madrid", "Berlin", "Amsterdam", "Prague", "Vienna", "Budapest",
            "Athens", "Istanbul", "Dubai", "Bangkok", "Singapore", "Sydney"
        ]
        
        message_lower = message.lower()
        for city in cities:
            if city.lower() in message_lower:
                return city
        return None
    
    def _extract_dates(self, message: str) -> Optional[Dict]:
        """Extract date patterns from message."""
        patterns = {
            "relative": r"(next|dans|in)\s+(week|semaine|month|mois)",
            "month": r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|january|february|march|april|may|june|july|august|september|october|november|december)",
            "specific": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        }
        
        for pattern_type, pattern in patterns.items():
            match = re.search(pattern, message.lower())
            if match:
                return {
                    "type": pattern_type,
                    "value": match.group(0)
                }
        return None
    
    def _extract_travelers(self, message: str) -> Optional[int]:
        """Extract number of travelers."""
        patterns = [
            r"(\d+)\s+(person|people|pers|personnes)",
            r"for\s+(\d+)",
            r"pour\s+(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return int(match.group(1))
        return None
    
    def _classify_budget(self, message: str) -> Optional[str]:
        """Classify budget level from keywords."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["cheap", "budget", "économique", "pas cher", "low cost"]):
            return "low"
        elif any(word in message_lower for word in ["luxury", "luxe", "premium", "expensive", "cher"]):
            return "high"
        elif any(word in message_lower for word in ["mid-range", "moyen", "reasonable", "modéré"]):
            return "medium"
        
        return None
    
    def _extract_preferences(self, message: str) -> List[str]:
        """Extract travel preferences."""
        preference_keywords = {
            "culture": ["culture", "museum", "musée", "historical", "historique"],
            "beach": ["beach", "plage", "sea", "mer", "ocean"],
            "business": ["business", "conference", "meeting", "affaires"],
            "relaxation": ["relax", "détente", "spa", "calm", "calme"],
            "adventure": ["adventure", "aventure", "hiking", "randonnée"],
            "gastronomy": ["food", "cuisine", "gastronomie", "restaurant"]
        }
        
        message_lower = message.lower()
        preferences = []
        
        for pref, keywords in preference_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                preferences.append(pref)
        
        return preferences
    
    def _fallback_analysis(self, message: str) -> Dict:
        """Complete fallback analysis without HF models."""
        intent = self._keyword_intent(message)
        entities = self._extract_entities(message)
        
        return {
            "intent": intent["label"],
            "confidence": intent["score"],
            "entities": entities,
            "raw_message": message
        }
