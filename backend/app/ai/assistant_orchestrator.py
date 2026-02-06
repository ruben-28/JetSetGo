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
        
        # Detect intent (ORDER MATTERS - check inspiration FIRST to avoid conflicts)
        # Inspiration has priority over package_search to handle "idée de voyage"
        if any(word in message_lower for word in ["idée", "idees", "inspiration", "suggest", "recommand", "conseil", "propose"]):
            intent = "inspiration"
        elif any(word in message_lower for word in ["vol", "vols", "flight", "avion", "fly", "voler"]):
            intent = "flight_search"
        elif any(word in message_lower for word in ["hotel", "hôtel", "hébergement", "accommodation", "logement"]):
            intent = "hotel_search"
        elif any(word in message_lower for word in ["package", "packages", "voyage", "séjour", "trip", "vacances"]):
            intent = "package_search"
        else:
            intent = "general"
        
        # Extract entities (simple approach)
        entities = self._extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities
        }
    
    def _extract_entities(self, message: str) -> Dict:
        """Extract destination, dates, travelers, period, preferences using simple patterns."""
        # List of major cities
        cities = [
            "Paris", "London", "New York", "Tokyo", "Rome", "Barcelona",
            "Madrid", "Berlin", "Amsterdam", "Prague", "Vienna", "Budapest",
            "Athens", "Istanbul", "Dubai", "Bangkok", "Singapore", "Sydney",
            "Los Angeles", "Miami", "Toronto", "Montreal", "Cancun", "Marrakech"
        ]
        
        message_lower = message.lower()
        
        destination = None
        for city in cities:
            if city.lower() in message_lower:
                destination = city
                break
        
        # Extract period/month
        months = {
            "janvier": "janvier", "février": "février", "mars": "mars", "avril": "avril",
            "mai": "mai", "juin": "juin", "juillet": "juillet", "août": "août",
            "septembre": "septembre", "octobre": "octobre", "novembre": "novembre", "décembre": "décembre",
            "january": "janvier", "february": "février", "march": "mars", "april": "avril",
            "may": "mai", "june": "juin", "july": "juillet", "august": "août",
            "september": "septembre", "october": "octobre", "november": "novembre", "december": "décembre"
        }
        
        period = None
        for month_key, month_val in months.items():
            if month_key in message_lower:
                period = month_val
                break
        
        # Extract preferences
        preferences = []
        if any(word in message_lower for word in ["soleil", "sun", "plage", "beach", "chaud", "warm"]):
            preferences.append("soleil/plage")
        if any(word in message_lower for word in ["culture", "musée", "museum", "histoire", "history"]):
            preferences.append("culture")
        if any(word in message_lower for word in ["nature", "montagne", "mountain", "randonnée", "hiking"]):
            preferences.append("nature")
        if any(word in message_lower for word in ["aventure", "adventure", "sport"]):
            preferences.append("aventure")
        
        return {
            "destination": destination,
            "period": period,
            "preferences": preferences,
            "dates": None,  # Can be enhanced with date parsing
            "travelers": None  # Can be enhanced
        }
    
    async def _generate_ollama_response(self, prompt_type: str, context: Dict) -> str:
        """Generate natural language response using Ollama."""
        
        # Build messages for Ollama chat API
        system_message = "Tu es un assistant de voyage intelligent et sympathique pour JetSetGo. Sois enthousiaste, mais reste équilibré et objectif, notamment concernant la sécurité et la situation politique."
        
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
            # Utiliser le contexte extrait
            period = context.get('period', '')
            prefs = context.get('preferences', [])
            user_msg = context.get('message', '')
            
            # Construire le texte contextualisé
            period_text = f" pour {period}" if period else ""
            prefs_text = f" (préférences: {', '.join(prefs)})" if prefs else ""
            
            user_prompt = (
                f"L'utilisateur dit : '{user_msg}'\n"
                f"CONTEXTE: Il cherche des idées de voyage{period_text}{prefs_text}.\n\n"
                f"INSTRUCTIONS :\n"
                f"1. Si la demande concerne un pays spécifique ou demande un avis (ex: 'est-ce que X est dangereux ?', 'avis sur Y') :\n"
                f"   - Donne une réponse, paragraphe par paragraphe, équilibrée et nuancée.\n"
                f"   - Mentionne EXPLICITEMENT les risques sécurité/politique si nécessaire.\n"
                f"   - NE PAS utiliser de format liste ni d'emojis.\n\n"
                f"2. Sinon (si l'utilisateur veut juste des idées) :\n"
                f"   - Suggère 3-4 destinations.\n"
                f"   - Format OBLIGATOIRE: Nom - raison courte.\n"
                f"   - N'utilise JAMAIS d'emojis."
            )
        
        else:  # general
            user_prompt = f"L'utilisateur dit : '{context.get('message', '')}'\nRéponds de manière sympathique mais sans utiliser d'emojis. Si la question porte sur la sécurité ou un avis (ex: Iran, Corée du Nord...), sois nuancé et mentionne les risques éventuels. Sois bref."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Create a fresh OllamaGateway for each request to avoid
            # client reuse issues (client is closed after context exit)
            async with OllamaGateway() as gateway:
                result = await gateway.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=650
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
        """Handle inspiration requests with contextualized suggestions."""
        # Pass extracted context to Ollama for personalized suggestions
        context = {
            "period": entities.get("period"),
            "preferences": entities.get("preferences", []),
            "message": user_message
        }
        
        response = await self._generate_ollama_response(
            "inspiration",
            context
        )
        
        return {
            "action": "chat_only",
            "target_view": None,
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {
                "inspiration": True,
                "context": context
            }
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
