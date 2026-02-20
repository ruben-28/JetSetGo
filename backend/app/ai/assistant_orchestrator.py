"""
Assistant Orchestrator - Moteur de Décision Central

Refactorisé pour utiliser l'infrastructure de gateway existante :
- app.gateway.OllamaGateway pour la génération de langage naturel
- app.gateway.HFGateway pour l'analyse (peut être étendu pour la classification d'intention)

Flux :
1. Recevoir le message utilisateur
2. Analyser l'intention (matching de mots-clés simple pour l'instant, peut intégrer modèles HF plus tard)
3. Décider de l'action basée sur l'intention
4. Générer la réponse en langage naturel avec Ollama
5. Retourner l'action + réponse au desktop
"""
from typing import Dict, Optional, List
import logging
from app.gateway.ollama_gateway import OllamaGateway
from app.gateway.huggingface_gateway import HuggingFaceGateway
from app.gateway.travel_provider import TravelProvider

logger = logging.getLogger(__name__)


class AssistantOrchestrator:
    """
    Moteur de décision central pour l'assistant IA.
    Utilise l'infrastructure de gateway existante.
    """
    
    def __init__(self):
        self.travel_provider = TravelProvider()
    
    async def process_message(self, user_message: str, user_id: int) -> Dict:
        """
        Logique d'orchestration principale.
        
        Retourne :
            {
                "action": str,  # "navigate", "display_results", "chat_only"
                "target_view": str | None,  # "flights", "hotels", "packages"
                "prefill_data": {...} | None,
                "search_results": [...] | None,
                "response_text": str,
                "metadata": {...}
            }
        """
        logger.info(f"Traitement du message de l'utilisateur {user_id} : {user_message}")
        
        # Étape 1 : Analyser l'intention en utilisant un simple matching de mots-clés
        # TODO : Peut être amélioré avec la classification zero-shot HF plus tard
        analysis = await self._analyze_intent(user_message)
        
        intent = analysis["intent"]
        entities = analysis["entities"]
        
        logger.info(f"Intention : {intent}, Entités : {entities}")
        
        # Étape 2 : Routage basé sur l'intention
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
            # Conversation générale
            return await self._handle_general_conversation(user_message)
    
    async def _analyze_intent(self, message: str) -> Dict:
        """
        Analyser l'intention en utilisant une approche hybride (HF Zero-Shot + Regex Fallback).
        """
        # 1. Essayer la classification Zero-Shot Hugging Face
        async with HuggingFaceGateway() as gateway:
            # Les candidats sont maintenant codés en dur dans le Gateway
            
            result = await gateway.classify_intent(message)
            
            # Format du résultat : {'intent': '...', 'confidence': 0.9}
            # La logique de seuil est déjà gérée dans le Gateway
            intent = result["intent"]
            confidence = result["confidence"]
            
            logger.info(f"Intention détectée '{intent}' avec confiance {confidence:.2f}")
                
        # 3. Extraire les entités (Hybride : HF NER + Regex)
        entities = await self._extract_entities(message)
        
        return {
            "intent": intent,
            "entities": entities
        }
    
    async def _extract_entities(self, message: str) -> Dict:
        """
        Extraction d'Entités Hybride :
        - LOC (Destination/Origine) : Utilise Hugging Face NER (xlm-roberta)
        - DATES/TRAVELERS : Utilise Regex (plus fiable pour la structure)
        """
        # 1. Extraction Regex (Dates, Voyageurs, Budget, Préférences)
        # Nous réutilisons la logique du mock/helper Gateway qui a de bons patterns regex
        # Ou l'implémentons ici. Pour une séparation propre, appelons les helpers du Gateway
        # via une méthode privée ou réimplémentons simplement des regex ici.
        # Gardons-le robuste et simple ici.
        
        # Regex de date (manuel pour l'instant pour éviter l'enfer des dépendances si dateparser manquant)
        import re
        date_pattern = r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|demain|semaine prochaine|\d{1,2}[/-]\d{1,2})"
        date_match = re.search(date_pattern, message.lower())
        dates = {"raw": date_match.group(0)} if date_match else None
        
        # 2. HF NER (pour Lieux - Locations)
        destination = None
        async with HuggingFaceGateway() as gateway:
            entities_list = await gateway.extract_entities(message)
            # Filtrer pour LOC
            locations = [e["word"] for e in entities_list if e.get("entity_group") == "LOC"]
            if locations:
                # Naïf : prendre le premier lieu comme destination
                destination = locations[0]
        
        # Fallback pour la destination si NER a échoué
        if not destination:
            # Liste des villes majeures (Fallback)
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
            "period": dates["raw"] if dates else None, # Compatibilité héritée
            "preferences": self._extract_preferences(message),
            "dates": dates,
            "travelers": None 
        }

    def _extract_preferences(self, message: str) -> List[str]:
        """Extraire les préférences de voyage via mots-clés."""
        preferences = []
        keywords = {
            "plage": ["plage", "mer", "sable", "allonger", "baignade"],
            "montagne": ["montagne", "ski", "randonnée", "alpes"],
            "famille": ["famille", "enfant", "enfants", "calme"],
            "couple": ["couple", "romantique", "amoureux"],
            "aventure": ["aventure", "sport", "sensation", "découverte", "exotique"],
            "pas cher": ["pas cher", "économique", "budget", "petit prix"],
            "luxe": ["luxe", "standing", "premium", "étoiles"],
            "culture": ["culture", "musée", "histoire", "monument"],
            "gastronomie": ["gastronomie", "manger", "restaurant", "cuisine"],
            "nature": ["nature", "vert", "campagne", "paysage"],
            "ville": ["ville", "shopping", "urbain", "métropole"]
        }
        
        message_lower = message.lower()
        for pref, kws in keywords.items():
            if any(kw in message_lower for kw in kws):
                preferences.append(pref)
                
        return preferences
    
    async def _generate_ollama_response(self, prompt_type: str, context: Dict) -> str:
        """Générer une réponse en langage naturel utilisant Ollama."""
        
        # Construire les messages pour l'API de chat Ollama
        # Forcer explicitement la langue française pour éviter les hallucinations/mélanges de langues
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
            dest = context.get('destination')
            user_msg = context.get('message', '')
            
            period_text = f"en {period}" if period else ""
            prefs_text = f", avec préférence pour : {', '.join(prefs)}" if prefs else ""

            # CAS 1 : Demande d'AVIS sur une destination spécifique (ex: "Iran", "Japon")
            if dest:
                user_prompt = (
                    f"L'utilisateur demande ton avis sur cette destination : '{dest}' ({period_text}).\n"
                    f"Message complet : '{user_msg}'\n\n"
                    f"Tâche : Donne une réponse structurée sur ce pays/ville.\n"
                    f"- Commence par une phrase d'accroche sur l'attractivité (beauté, culture...).\n"
                    f"- Paragraphe 1 : Pourquoi c'est bien (points forts).\n"
                    f"- Paragraphe 2 : Sécurité et vigilance (sois franc s'il y a des risques politiques/géopolitiques).\n"
                    f"- Termine par une phrase de conclusion.\n\n"
                    f"Règles :\n"
                    f"- Pas de liste de suggestions d'autres pays.\n"
                    f"- Réponse équilibrée et objective.\n"
                    f"- Langue : français uniquement. Pas d'emojis."
                )

            # CAS 2 : Demande de SUGGESTIONS (ex: "Où partir ?")
            else:
                user_prompt = (
                    f"L'utilisateur demande : '{user_msg}'\n"
                    f"Période : {period_text or 'non précisée'}{prefs_text}\n\n"
                    f"Réponds en proposant des idées structurées par catégories. Pour chaque catégorie, tu DOIS lister 2 ou 3 destinations précises avec des tirets.\n\n"
                    f"1) Mer / soleil :\n- [Destination 1] : [Pourquoi]\n- [Destination 2] : [Pourquoi]\n\n"
                    f"2) Ski / montagne :\n- [Destination 1] : [Pourquoi]\n- [Destination 2] : [Pourquoi]\n\n"
                    f"3) City trip :\n- [Ville 1] : [Pourquoi]\n- [Ville 2] : [Pourquoi]\n\n"
                    f"4) Nature / aventure :\n- [Destination 1] : [Pourquoi]\n- [Destination 2] : [Pourquoi]\n\n"
                    f"Règles :\n"
                    f"- OBLIGATOIRE : Utilise des tirets (-) pour lister les destinations.\n"
                    f"- Suggestion DOIT être un lieu précis (Ville, Pays, Région), pas juste 'La Méditerranée'.\n"
                    f"- Pas de blabla général avant ou après les listes.\n"
                    f"- Termine par 2 questions pour affiner (budget, durée).\n"
                    f"- Langue : français uniquement. Pas d'emojis."
                )
        
        else:  # general
            user_prompt = f"L'utilisateur dit : '{context.get('message', '')}'\nRéponds EN FRANÇAIS. Sois sympathique mais sans utiliser d'emojis. Si la question porte sur la sécurité ou un avis, sois nuancé. Sois bref."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Créer un OllamaGateway frais pour chaque requête pour éviter
            # les problèmes de réutilisation de client (client est fermé après sortie de contexte)
            async with OllamaGateway() as gateway:
                # print(f"DEBUG PROMPT:\n{messages}\n")
                
                result = await gateway.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=650
                )
                
                # print(f"DEBUG RESPONSE:\n{result['content']}\n")
                
                return result["content"]
        
        except Exception as e:
            logger.error(f"Génération Ollama échouée : {e}")
            # Fallback vers des templates simples
            return self._fallback_response(prompt_type, context)
    
    def _fallback_response(self, prompt_type: str, context: Dict) -> str:
        """Solution de repli lorsque Ollama est indisponible."""
        dest = context.get('destination', 'votre destination')
        
        fallbacks = {
            "navigate_to_flights": f"Je vous amène à la recherche de vols pour {dest}.",
            "navigate_to_hotels": f"Je vous amène à la recherche d'hôtels à {dest}.",
            "navigate_to_packages": f"Je vous amène à la recherche de packages pour {dest}.",
            "clarification": "Pouvez-vous me donner plus de détails ?",
            "inspiration": self._fallback_inspiration(context),
            "general": "Comment puis-je vous aider dans votre voyage ?"
        }
        
        return fallbacks.get(prompt_type, fallbacks["general"])
    
    def _fallback_inspiration(self, context: Dict) -> str:
        """Fallback contextuel pour l'inspiration quand Ollama est indisponible."""
        dest = context.get('destination')
        prefs = context.get('preferences', [])
        period = context.get('period', '')
        
        # Si c'est une demande d'avis sur une destination précise
        if dest:
            return (
                f"Je ne peux pas accéder aux informations détaillées sur **{dest}** pour le moment.\n\n"
                f"En général, il est conseillé de vérifier :\n"
                f"- Les conditions de sécurité sur le site France Diplomatie.\n"
                f"- La météo pour la période concernée.\n\n"
                f"Voulez-vous que je cherche des vols pour {dest} ?"
            )

        # Suggestions par préférence
        suggestions_map = {
            "plage": [
                "**Nice** - Plages magnifiques sur la Cote d'Azur",
                "**Bali** - Plages de sable fin et eaux cristallines",
                "**Crete** - Plages paradisiaques en Mediterranee",
                "**Cancun** - Plages de reve et mer turquoise",
            ],
            "montagne": [
                "**Chamonix** - Au pied du Mont-Blanc, randonnees exceptionnelles",
                "**Zermatt** - Vue imprenable sur le Cervin",
                "**Innsbruck** - Alpes autrichiennes, nature preservee",
                "**Whistler** - Montagnes canadiennes spectaculaires",
            ],
            "culture": [
                "**Rome** - Art, histoire et gastronomie italienne",
                "**Kyoto** - Temples anciens et jardins zen",
                "**Athenes** - Berceau de la civilisation occidentale",
                "**Istanbul** - Carrefour des cultures",
            ],
        }
        
        # Trouver des suggestions correspondantes
        destinations = []
        for pref in prefs:
            if pref in suggestions_map:
                destinations.extend(suggestions_map[pref])
                break
        
        if not destinations:
            destinations = [
                "**Barcelone** - Plages, architecture, vie nocturne",
                "**Paris** - Culture, gastronomie, monuments historiques",
                "**Tokyo** - Technologie, temples, cuisine exceptionnelle",
                "**New York** - Ville dynamique, shopping, arts",
            ]
        
        period_text = f" en {period}" if period else ""
        result = f"Voici quelques destinations{period_text} :\n\n"
        result += "\n".join(destinations[:4])
        result += "\n\nLaquelle vous interesse ?"
        return result
    
    async def _handle_flight_search(self, entities: Dict, user_message: str) -> Dict:
        """Gérer l'intention de recherche de vol."""
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
        
        # Naviguer vers la vue vols avec destination pré-remplie
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
        """Gérer l'intention de recherche d'hôtel."""
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
        """Gérer l'intention de recherche de package."""
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
        """Gérer les demandes d'inspiration avec suggestions contextualisées."""
        # Passer le contexte extrait à Ollama pour des suggestions personnalisées
        context = {
            "period": entities.get("period"),
            "preferences": entities.get("preferences", []),
            "destination": entities.get("destination"),
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
        """Gérer l'intention d'historique de réservation."""
        # Naviguer vers la vue historique
        response = await self._generate_ollama_response(
            "general", # Confirmation générique
            {"message": "Je vous affiche votre historique de réservations."}
        )
        return {
            "action": "navigate",
            "target_view": "history", # En supposant que cette vue existe
            "prefill_data": None,
            "search_results": None,
            "response_text": response,
            "metadata": {"intent": "booking_history"}
        }

    async def _handle_budget_advice(self, entities: Dict, user_message: str) -> Dict:
        """Gérer l'intention de conseil budgétaire."""
        # Chat uniquement pour l'instant
        response = await self._generate_ollama_response(
            "general",
            {"message": user_message} # Laisser Ollama gérer le conseil
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
        """Gérer la conversation générale."""
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
