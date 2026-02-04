"""
Assistant Orchestrator - Central Decision Engine

Refactored to use existing gateway infrastructure:
- app.gateway.OllamaGateway for natural language generation
- app.gateway.HFGateway for analysis (can be extended for intent classification)

Flow:
1. Receive user message
2. Analyze intent (simple keyword matching for now, can integrate HF models later)
3. Decide action based on intent
4. Generate natural language response with Ollama
5. Return action + response to desktop
"""
from typing import Dict, Optional, List
import logging
from app.gateway.ollama_gateway import OllamaGateway
from app.gateway.travel_provider import TravelProvider

logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """
    Central decision engine for AI assistant.
    Uses existing gateway infrastructure.
    """
    
    def __init__(self):
        self.ollama = OllamaGateway()
        self.travel_provider = TravelProvider()
    
    async def process_message(self, user_message: str, user_id: int) -> Dict:
        """
        Main orchestration logic.
        
        Returns:
            {
                "action": str,  # "navigate", "display_results", "chat_only"
                "target_view": str | None,  # "flights", "hotels", "packages"
                "prefill_data": {...} | None,
                "search_results": [...] | None,
                "response_text": str,
                "metadata": {...}
            }
        """
        logger.info(f"Processing message from user {user_id}: {user_message}")
        
        # Step 1: Analyze intent using simple keyword matching
        # TODO: Can be enhanced with HF zero-shot classification later
        analysis = self._analyze_intent(user_message)
        
        intent = analysis["intent"]
        entities = analysis["entities"]
        
        logger.info(f"Intent: {intent}, Entities: {entities}")
        
        # Step 2: Route based on intent
        if intent == "flight_search":
            return await self._handle_flight_search(entities, user_message)
        
        elif intent == "hotel_search":
            return await self._handle_hotel_search(entities, user_message)
        
        elif intent == "package_search":
            return await self._handle_package_search(entities, user_message)
        
        elif intent == "inspiration":
            return await self._handle_inspiration(entities, user_message)
        
        else:
            # General conversation
            return await self._handle_general_conversation(user_message)
    
    def _analyze_intent(self, message: str) -> Dict:
        """
        Simple keyword-based intent detection.
        Can be enhanced with HuggingFace models.
        """
        message_lower = message.lower()
        
        # Detect intent
        if any(word in message_lower for word in ["vol", "vols", "flight", "avion", "fly", "voler"]):
            intent = "flight_search"
        elif any(word in message_lower for word in ["hotel", "hôtel", "hébergement", "accommodation", "logement"]):
            intent = "hotel_search"
        elif any(word in message_lower for word in ["package", "packages", "voyage", "séjour", "trip", "vacances"]):
            intent = "package_search"
        elif any(word in message_lower for word in ["idée", "idees", "inspiration", "suggest", "recommand", "conseil"]):
            intent = "inspiration"
        else:
            intent = "general"
        
        # Extract entities (simple approach)
        entities = self._extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities
        }
    
    def _extract_entities(self, message: str) -> Dict:
        """Extract destination, dates, travelers using simple patterns."""
        # List of major cities
        cities = [
            "Paris", "London", "New York", "Tokyo", "Rome", "Barcelona",
            "Madrid", "Berlin", "Amsterdam", "Prague", "Vienna", "Budapest",
            "Athens", "Istanbul", "Dubai", "Bangkok", "Singapore", "Sydney",
            "Los Angeles", "Miami", "Toronto", "Montreal", "Cancun", "Marrakech"
        ]
        
        destination = None
        for city in cities:
            if city.lower() in message.lower():
                destination = city
                break
        
        return {
            "destination": destination,
            "dates": None,  # Can be enhanced
            "travelers": None  # Can be enhanced
        }
    
    async def _generate_ollama_response(self, prompt_type: str, context: Dict) -> str:
        """Generate natural language response using Ollama."""
        
        # Build messages for Ollama chat API
        system_message = "Tu es un assistant de voyage intelligent et sympathique pour JetSetGo."
        
        if prompt_type == "navigate_to_flights":
            user_prompt = f"L'utilisateur veut chercher des vols pour {context.get('destination', 'une destination')}. Confirme que tu vas l'amener à la recherche de vols. Sois bref (1 phrase)."
        
        elif prompt_type == "navigate_to_hotels":
            user_prompt = f"L'utilisateur veut chercher des hôtels à {context.get('destination', 'une destination')}. Confirme que tu vas l'amener à la recherche d'hôtels. Sois bref (1 phrase)."
        
        elif prompt_type == "navigate_to_packages":
            user_prompt = f"L'utilisateur veut chercher des packages pour {context.get('destination', 'une destination')}. Confirme que tu vas l'amener à la recherche de packages. Sois bref (1 phrase)."
        
        elif prompt_type == "clarification":
            missing = context.get('missing', 'une information')
            user_prompt = f"Demande poliment à l'utilisateur de préciser {missing}. Sois bref (1 phrase)."
        
        elif prompt_type == "inspiration":
            user_prompt = (
                "L'utilisateur cherche de l'inspiration pour un voyage. "
                "Tu DOIS suggérer 2-3 destinations concrètes avec leurs points forts. "
                "Ne pose PAS de question, donne directement des suggestions. "
                "Format: [Destination] - [Points forts]. "
                "Sois enthousiaste et concis (3-4 phrases max). "
                "Exemple: 'Je vous suggère Paris pour sa culture et sa gastronomie, Tokyo pour...'"
            )
        
        else:  # general
            user_prompt = f"Réponds à: {context.get('message', '')}. Sois sympathique et bref (1-2 phrases)."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Use existing Ollama gateway with proper lifecycle
            async with self.ollama as gateway:
                result = await gateway.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150
                )
                return result["content"]
        
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            # Fallback to simple templates
            return self._fallback_response(prompt_type, context)
    
    def _fallback_response(self, prompt_type: str, context: Dict) -> str:
        """Fallback when Ollama is unavailable."""
        dest = context.get('destination', 'votre destination')
        
        fallbacks = {
            "navigate_to_flights": f"Je vous amène à la recherche de vols pour {dest}.",
            "navigate_to_hotels": f"Je vous amène à la recherche d'hôtels à {dest}.",
            "navigate_to_packages": f"Je vous amène à la recherche de packages pour {dest}.",
            "clarification": "Pouvez-vous me donner plus de détails ?",
            "inspiration": (
                "Voici quelques destinations populaires :\n\n"
                "🗼 **Paris** - Culture, gastronomie, monuments historiques\n"
                "🗾 **Tokyo** - Technologie, temples, cuisine exceptionnelle\n"
                "🗽 **New York** - Ville dynamique, shopping, arts\n"
                "🏖️ **Barcelone** - Plages, architecture, vie nocturne\n\n"
                "Laquelle vous intéresse ?"
            ),
            "general": "Comment puis-je vous aider dans votre voyage ?"
        }
        
        return fallbacks.get(prompt_type, fallbacks["general"])
    
    async def _handle_flight_search(self, entities: Dict, user_message: str) -> Dict:
        """Handle flight search intent."""
        destination = entities.get("destination")
        
        if not destination:
            response = await self._generate_ollama_response(
                "clarification",
                {"missing": "la destination"}
            )
            return {
                "action": "chat_only",
                "target_view": None,
                "prefill_data": None,
                "search_results": None,
                "response_text": response,
                "metadata": {"needs_clarification": True}
            }
        
        # Navigate to flights view with prefilled destination
        response = await self._generate_ollama_response(
            "navigate_to_flights",
            {"destination": destination}
        )
        
        return {
            "action": "navigate",
            "target_view": "flights",
            "prefill_data": {"destination": destination},
            "search_results": None,
            "response_text": response,
            "metadata": {"destination": destination}
        }
    
    async def _handle_hotel_search(self, entities: Dict, user_message: str) -> Dict:
        """Handle hotel search intent."""
        destination = entities.get("destination")
        
        if not destination:
            response = await self._generate_ollama_response(
                "clarification",
                {"missing": "la ville"}
            )
            return {
                "action": "chat_only",
                "target_view": None,
                "prefill_data": None,
                "search_results": None,
                "response_text": response,
                "metadata": {"needs_clarification": True}
            }
        
        response = await self._generate_ollama_response(
            "navigate_to_hotels",
            {"destination": destination}
        )
        
        return {
            "action": "navigate",
            "target_view": "hotels",
            "prefill_data": {"destination": destination},
            "search_results": None,
            "response_text": response,
            "metadata": {"destination": destination}
        }
    
    async def _handle_package_search(self, entities: Dict, user_message: str) -> Dict:
        """Handle package search intent."""
        destination = entities.get("destination")
        
        if not destination:
            response = await self._generate_ollama_response(
                "clarification",
                {"missing": "la destination"}
            )
            return {
                "action": "chat_only",
                "target_view": None,
                "prefill_data": None,
                "search_results": None,
                "response_text": response,
                "metadata": {"needs_clarification": True}
            }
        
        response = await self._generate_ollama_response(
            "navigate_to_packages",
            {"destination": destination}
        )
        
        return {
            "action": "navigate",
            "target_view": "packages",
            "prefill_data": {"destination": destination},
            "search_results": None,
            "response_text": response,
            "metadata": {"destination": destination}
        }
    
    async def _handle_inspiration(self, entities: Dict, user_message: str) -> Dict:
        """Handle inspiration requests."""
        response = await self._generate_ollama_response(
            "inspiration",
            {}
        )
        
        return {
            "action": "chat_only",
            "target_view": None,
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {"inspiration": True}
        }
    
    async def _handle_general_conversation(self, user_message: str) -> Dict:
        """Handle general conversation."""
        response = await self._generate_ollama_response(
            "general",
            {"message": user_message}
        )
        
        return {
            "action": "chat_only",
            "target_view": None,
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {}
        }
