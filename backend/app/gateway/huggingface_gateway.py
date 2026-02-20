from typing import Dict, List, Optional, Any
from huggingface_hub import InferenceClient
from .base_gateway import BaseGateway

class HuggingFaceGateway(BaseGateway):
    """
    Gateway pour l'intégration de l'API d'inférence HuggingFace via InferenceClient.
    """
    
    INTENT_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    NER_MODEL = "Davlan/xlm-roberta-base-ner-hrl"
    
    def _get_required_config_keys(self) -> list[str]:
        return ["HF_API_TOKEN"]

    async def _get_client(self) -> InferenceClient:
        """Obtenir ou créer InferenceClient"""
        token = self._get_config("HF_API_TOKEN")
        return InferenceClient(provider="hf-inference", api_key=token)

    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classifier l'intention en utilisant la classification Zero-Shot."""
        if self.is_mock_mode():
            return await self._mock_classify_intent(text)

        candidates = [
            "flight_search", "hotel_search", "package_search",
            "booking_history", "budget_advice", "inspiration", "general"
        ]

        try:
            # 1. Vérification rapide par mots-clés pour les cas difficiles (Inspiration)
            inspiration_keywords = ["conseil", "partir ou", "où partir", "destination", "idée de voyage", "meilleur endroit"]
            if any(kw in text.lower() for kw in inspiration_keywords):
                self.logger.info(f"Intention 'inspiration' détectée par mots-clés pour: {text}")
                return {"intent": "inspiration", "confidence": 1.0}

            client = await self._get_client()
            # Note : zero_shot_classification n'est pas asynchrone dans le client actuel,
            # mais généralement assez rapide ou devrait être enveloppé dans run_in_executor si bloquant.
            # Cependant, pour la simplicité et selon la demande utilisateur d'utiliser le client :
            
            # Envelopper le texte dans une liste pour éviter l'erreur de validation de type strict 
            # dans les versions plus récentes de huggingface_hub qui attendent une liste en sortie lors de la validation.
            results = client.zero_shot_classification(
                [text],
                candidates,
                model=self.INTENT_MODEL
            )
            
            # Le résultat est généralement {labels: [], scores: []} ou un objet similaire
            # InferenceClient retourne généralement un objet de type dict
            
            if not results:
                return {"intent": "general", "confidence": 0.0}

            # Obtenir le premier résultat
            result = results[0]

            # Accéder aux attributs en supposant qu'il retourne un objet ou un dictionnaire
            # Basé sur la doc, il retourne un dict avec 'labels' et 'scores'
            # Ajuster l'accès selon le type de retour réel si nécessaire.
            
            # Obtenir le premier élément en toute sécurité
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            
            if top_score < 0.55:
                top_label = "general"
                
            return {
                "intent": top_label,
                "confidence": top_score
            }

        except Exception as e:
            self.logger.error(f"Échec de la classification d'intention HF : {e}")
            return await self._mock_classify_intent(text)

    async def extract_entities(self, text: str) -> List[Dict]:
        """Extraire les entités nommées en utilisant la classification de tokens (Token Classification)."""
        if self.is_mock_mode():
            return await self._mock_extract_entities(text)
            
        try:
            client = await self._get_client()
            result = client.token_classification(text, model=self.NER_MODEL)
            
            # Le résultat est une liste d'objets/dicts
            # Normaliser vers notre format attendu
            entities = []
            for item in result:
                # item peut être un objet ou un dict
                # L'exemple utilisateur montrait `result = client.token_classification(...)`
                # Supposons une liste de dicts : {'entity_group': '..', 'word': '..', 'score': ..}
                # Mais le modèle 'Davlan' utilise 'PER', 'LOC', 'ORG'
                
                # Vérifier l'accès dict ou objet
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
            self.logger.error(f"Échec HF NER : {e}")
            return await self._mock_extract_entities(text)

    # ========================================================================
    # Mock / Solutions de repli (Fallback)
    # ========================================================================

    async def _mock_classify_intent(self, text: str) -> Dict[str, Any]:
        """Solution de repli simple par mots-clés."""
        text = text.lower()
        keywords = {
            "flight_search": ["vol", "flight", "avion", "fly"],
            "hotel_search": ["hotel", "hôtel", "hébergement"],
            "package_search": ["package", "séjour", "all inclusive"],
            "booking_history": ["réservation", "booking", "mes voyages", "historique"],
            "budget_advice": ["budget", "prix", "cher", "coût"],
            "inspiration": [
                "idée", "whereto", "suggestion", "conseil", "vacances", "partir ou", 
                "où partir", "destination", "recommandation", "meilleur endroit"
            ]
        }
        
        detected_intent = "general"
        
        # Prioriser l'inspiration si des mots clés forts sont présents
        if any(kw in text for kw in keywords["inspiration"]):
            return {"intent": "inspiration", "confidence": 0.9}
            
        match_count = 0
        for intent, kws in keywords.items():
            if intent == "inspiration": continue # Déjà traité
            for kw in kws:
                if kw in text:
                    detected_intent = intent
                    match_count += 1
                    break 
            if match_count > 0: break
        
        confidence = 0.8 if match_count > 0 else 0.0
        return {"intent": detected_intent, "confidence": confidence}

    async def _mock_extract_entities(self, text: str) -> List[Dict]:
        """Solution de repli simple par mots-clés pour le NER."""
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

