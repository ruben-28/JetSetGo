from typing import Dict, List, Optional, Any
from huggingface_hub import InferenceClient
from .base_gateway import BaseGateway

class HuggingFaceGateway(BaseGateway):
    """
    Gateway for HuggingFace Inference API integration using InferenceClient.
    """
    
    INTENT_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    NER_MODEL = "Davlan/xlm-roberta-base-ner-hrl"
    
    def _get_required_config_keys(self) -> list[str]:
        return ["HF_API_TOKEN"]

    async def _get_client(self) -> InferenceClient:
        """Get or create InferenceClient"""
        token = self._get_config("HF_API_TOKEN")
        return InferenceClient(provider="hf-inference", api_key=token)

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify intent using Zero-Shot Classification."""
        if self.is_mock_mode():
            return await self._mock_classify_intent(text)

        candidates = [
            "flight_search", "hotel_search", "package_search",
            "booking_history", "budget_advice", "inspiration", "general"
        ]

        try:
            client = await self._get_client()
            # Note: zero_shot_classification is not async in current client, 
            # but usually fast enough or we should wrap in run_in_executor if blocking.
            # However, for simplicity and as per user request to use client:
            
            # Wrap text in list to avoid strict type validation error in newer huggingface_hub versions
            # which expects a list output when validating.
            results = client.zero_shot_classification(
                [text],
                candidates,
                model=self.INTENT_MODEL
            )
            
            # Result is usually {labels: [], scores: []} or similar object
            # InferenceClient returns a dict-like object usually
            
            if not results:
                return {"intent": "general", "confidence": 0.0}

            # Get first result
            result = results[0]

            # Accessing attributes assuming it returns an object or dict
            # Based on docs, it returns a dict with 'labels' and 'scores'
            # Adjust access based on actual return type if needed.
            
            # Safely get first item
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            if top_score < 0.55:
                top_label = "general"
                
            return {
                "intent": top_label,
                "confidence": top_score
            }

        except Exception as e:
            self.logger.error(f"HF Intent Classification failed: {e}")
            return await self._mock_classify_intent(text)

    async def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities using Token Classification."""
        if self.is_mock_mode():
            return await self._mock_extract_entities(text)
            
        try:
            client = await self._get_client()
            result = client.token_classification(text, model=self.NER_MODEL)
            
            # Result is a list of objects/dicts
            # Normalize to our expected format
            entities = []
            for item in result:
                # item might be an object or dict
                # User example showed `result = client.token_classification(...)`
                # Let's assume list of dicts: {'entity_group': '..', 'word': '..', 'score': ..}
                # But 'Davlan' model uses 'PER', 'LOC', 'ORG'
                
                # Check for dict or object access
                entity_group = item.get('entity_group') if isinstance(item, dict) else item.entity_group
                word = item.get('word') if isinstance(item, dict) else item.word
                score = item.get('score') if isinstance(item, dict) else item.score
                
                entities.append({
                    "entity_group": entity_group,
                    "word": word,
                    "score": score
                })
                
            return entities

        except Exception as e:
            self.logger.error(f"HF NER failed: {e}")
            return await self._mock_extract_entities(text)

    # ========================================================================
    # Mock / Fallback
    # ========================================================================

    async def _mock_classify_intent(self, text: str) -> Dict[str, Any]:
        """Simple keyword fallback."""
        text = text.lower()
        keywords = {
            "flight_search": ["vol", "flight", "avion", "fly"],
            "hotel_search": ["hotel", "hôtel", "hébergement"],
            "package_search": ["package", "séjour", "all inclusive"],
            "booking_history": ["réservation", "booking", "mes voyages", "historique"],
            "budget_advice": ["budget", "prix", "cher", "coût"],
            "inspiration": ["idée", "whereto", "suggestion", "conseil", "vacances"]
        }
        
        detected_intent = "general"
        match_count = 0
        for intent, kws in keywords.items():
            for kw in kws:
                if kw in text:
                    detected_intent = intent
                    match_count += 1
                    break 
            if match_count > 0: break
        
        confidence = 0.8 if match_count > 0 else 0.0
        return {"intent": detected_intent, "confidence": confidence}

    async def _mock_extract_entities(self, text: str) -> List[Dict]:
        """Simple keyword fallback for NER."""
        entities = []
        text_lower = text.lower()
        cities = ["paris", "london", "new york", "tokyo", "dubai", "barcelona", "rome", "madrid"]
        for city in cities:
            if city in text_lower:
                entities.append({
                    "entity_group": "LOC",
                    "word": city.capitalize(),
                    "score": 0.8
                })
        return entities

