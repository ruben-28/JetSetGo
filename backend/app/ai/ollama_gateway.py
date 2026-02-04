"""
Ollama Gateway - Natural Language Generation Layer

Responsibilities:
- Generate human-friendly explanations
- Summarize search results
- Provide travel recommendations
- Format clarification questions

NOT responsible for:
- Intent detection (HF does this)
- Decision making (orchestrator does this)
- Entity extraction (HF does this)
"""
import httpx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaGateway:
    """Natural language generation using local Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"  # Can be changed to "mistral", "phi", etc.
    
    async def generate_response(self, prompt_type: str, context: Dict) -> str:
        """
        Generate natural language response based on structured context.
        
        Args:
            prompt_type: Type of prompt template to use
            context: Structured data to fill template
        
        Returns:
            Natural language response string
        """
        prompt = self._build_prompt(prompt_type, context)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": 200
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
                    return self._fallback_response(prompt_type, context)
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._fallback_response(prompt_type, context)
    
    def _build_prompt(self, prompt_type: str, context: Dict) -> str:
        """Build structured prompt for Ollama."""
        
        templates = {
            "flight_results": """You are a helpful travel assistant. Based on the following search results:
- Destination: {destination}
- Number of flights found: {num_results}
- Cheapest option: {cheapest_price}€
- Fastest option: {fastest_duration} minutes

Provide a brief, friendly summary (2-3 sentences) highlighting the best options.
Be concise and helpful.""",
            
            "hotel_results": """You are a helpful travel assistant. Based on the following hotel search:
- City: {city}
- Number of hotels found: {num_results}
- Cheapest option: {cheapest_price}€
- Best rated: {best_rating} stars

Provide a brief, friendly summary (2-3 sentences) highlighting the best options.
Be concise and helpful.""",
            
            "clarification": """You are a helpful travel assistant. The user wants to {intent}, 
but didn't specify the {missing}.

Ask them politely for this information in a natural, conversational way.
Be brief (1 sentence).""",
            
            "navigate_to_search": """You are a helpful travel assistant. The user wants to search for {view} 
to {destination}.

Acknowledge their request and let them know you're opening the search page 
with {destination} pre-filled.
Be friendly and brief (1 sentence).""",
            
            "inspiration": """You are a travel expert. The user is looking for travel inspiration with:
- Preferences: {preferences}
- Budget level: {budget}

Suggest 2-3 destinations that match these preferences.
Be enthusiastic and helpful, but concise (3-4 sentences max).""",
            
            "booking_summary": """You are a helpful travel assistant. Summarize this booking:
- Type: {booking_type}
- Destination: {destination}
- Price: {price}€
- Dates: {dates}

Confirm the booking in a friendly, professional way (2 sentences).""",
            
            "general": """You are a helpful travel assistant for JetSetGo.
The user said: {message}

Respond in a friendly, helpful way. Be concise (1-2 sentences)."""
        }
        
        template = templates.get(prompt_type, templates["general"])
        
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context key: {e}")
            return template.format(message=context.get("message", ""))
    
    def _fallback_response(self, prompt_type: str, context: Dict) -> str:
        """Fallback responses when Ollama is unavailable."""
        
        fallbacks = {
            "flight_results": f"J'ai trouvé {context.get('num_results', 0)} vols pour {context.get('destination', 'votre destination')}.",
            "hotel_results": f"J'ai trouvé {context.get('num_results', 0)} hôtels à {context.get('city', 'votre destination')}.",
            "clarification": "Pouvez-vous me donner plus de détails ?",
            "navigate_to_search": f"Je vous amène à la recherche de {context.get('view', 'voyages')}.",
            "inspiration": "Voici quelques destinations populaires : Paris, New York, Tokyo, Barcelone.",
            "booking_summary": "Votre réservation a été confirmée.",
            "general": "Je suis votre assistant de voyage JetSetGo. Comment puis-je vous aider ?"
        }
        
        return fallbacks.get(prompt_type, fallbacks["general"])
