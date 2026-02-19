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
from app.gateway.huggingface_gateway import HuggingFaceGateway
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
        analysis = await self._analyze_intent(user_message)
        
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
        
        elif intent == "booking_history":
            return await self._handle_booking_history(entities, user_message)
            
        elif intent == "budget_advice":
            return await self._handle_budget_advice(entities, user_message)
        
        elif intent == "inspiration":
            return await self._handle_inspiration(entities, user_message)
        
        else:
            # General conversation
            return await self._handle_general_conversation(user_message)
    
    async def _analyze_intent(self, message: str) -> Dict:
        """
        Analyze intent using Hybrid approach (HF Zero-Shot + Regex Fallback).
        """
        # 1. Try Hugging Face Zero-Shot Classification
        async with HuggingFaceGateway() as gateway:
            # Candidates are now hardcoded in the Gateway
            
            result = await gateway.classify_intent(message)
            
            # Result format: {'intent': '...', 'confidence': 0.9}
            # Threshold logic is already handled in the Gateway
            intent = result["intent"]
            confidence = result["confidence"]
            
            logger.info(f"Detected intent '{intent}' with confidence {confidence:.2f}")
                
        # 3. Extract entities (Hybrid: HF NER + Regex)
        entities = await self._extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities
        }
    
    async def _extract_entities(self, message: str) -> Dict:
        """
        Hybrid Entity Extraction:
        - LOC (Destination/Origin): Uses Hugging Face NER (xlm-roberta)
        - DATES/TRAVELERS: Uses Regex (more reliable for structure)
        """
        # 1. Regex Extraction (Dates, Travelers, Budget, Preferences)
        # We reuse the logic from the Gateway mock/helper which has good regex patterns
        # Or implement it here. For clean separation, let's call the Gateway's helpers
        # via a private method or just reimplement simple regex here.
        # Let's keep it robust and simple here.
        
        # Date regex (manual for now to avoid dependency hell if dateparser missing)
        import re
        date_pattern = r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|demain|semaine prochaine|\d{1,2}[/-]\d{1,2})"
        date_match = re.search(date_pattern, message.lower())
        dates = {"raw": date_match.group(0)} if date_match else None
        
        # 2. HF NER (for Locations)
        destination = None
        async with HuggingFaceGateway() as gateway:
            entities_list = await gateway.extract_entities(message)
            # Filter for LOC
            locations = [e["word"] for e in entities_list if e.get("entity_group") == "LOC"]
            if locations:
                # Naive: take first location as destination
                destination = locations[0]
        
        # Fallback for destination if NER failed
        if not destination:
            # List of major cities (Fallback)
            cities = [
                "Paris", "London", "New York", "Tokyo", "Rome", "Barcelona",
                "Madrid", "Berlin", "Amsterdam", "Prague", "Vienna", "Budapest",
                "Athens", "Istanbul", "Dubai", "Bangkok", "Singapore", "Sydney",
                "Los Angeles", "Miami", "Toronto", "Montreal", "Cancun", "Marrakech"
            ]
            for city in cities:
                if city.lower() in message.lower():
                    destination = city
                    break

        return {
            "destination": destination,
            "period": dates["raw"] if dates else None, # Legacy compatibility
            "preferences": [], # Can be enhanced later
            "dates": dates,
            "travelers": None 
        }
    
    async def _generate_ollama_response(self, prompt_type: str, context: Dict) -> str:
        """Generate natural language response using Ollama."""
        
        # Build messages for Ollama chat API
        # Explicitly enforce French language to avoid hallucinations/language mixing
        system_message = (
            "Tu es un assistant de voyage intelligent et sympathique pour JetSetGo. "
            "Ta langue de sortie est STRICTEMENT le FRANÇAIS. "
            "Même si l'utilisateur parle anglais ou une autre langue, tu dois répondre en français. "
            "Sois enthousiaste, mais reste équilibré et objectif, notamment concernant la sécurité et la situation politique."
        )
        
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
                f"   - Donne une réponse EN FRANÇAIS uniquement.\n"
                f"   - Fais des paragraphes, sois équilibré et nuancé.\n"
                f"   - Mentionne EXPLICITEMENT les risques sécurité/politique si nécessaire.\n"
                f"   - NE PAS utiliser de format liste ni d'emojis.\n\n"
                f"2. Sinon (si l'utilisateur veut juste des idées) :\n"
                f"   - Suggère 3-4 destinations.\n"
                f"   - Format OBLIGATOIRE: Nom - raison courte.\n"
                f"   - N'utilise JAMAIS d'emojis."
            )
        
        else:  # general
            user_prompt = f"L'utilisateur dit : '{context.get('message', '')}'\nRéponds EN FRANÇAIS. Sois sympathique mais sans utiliser d'emojis. Si la question porte sur la sécurité ou un avis (ex: Iran, Corée du Nord...), sois nuancé et mentionne les risques éventuels. Sois bref."
        
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
    
    async def _handle_booking_history(self, entities: Dict, user_message: str) -> Dict:
        """Handle booking history intent."""
        # Navigate to history view
        response = await self._generate_ollama_response(
            "general", # Generic confirmation
            {"message": "Je vous affiche votre historique de réservations."}
        )
        return {
            "action": "navigate",
            "target_view": "history", # Assuming this view exists
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {"intent": "booking_history"}
        }

    async def _handle_budget_advice(self, entities: Dict, user_message: str) -> Dict:
        """Handle budget advice intent."""
        # Chat only for now
        response = await self._generate_ollama_response(
            "general",
            {"message": user_message} # Let Ollama handle the advice
        )
        return {
            "action": "chat_only",
            "target_view": None,
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {"intent": "budget_advice"}
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
            "metadata": {"intent": "general"}
        }
