"""
Module Gateway Ollama
Implémentation du fournisseur LLM pour le serveur Ollama local.
"""

import os
import logging
from typing import Dict, Any, List, Optional

from .base_gateway import BaseGateway, GatewayError, GatewayTimeoutError, GatewayAPIError
from .llm_provider import LLMProvider


logger = logging.getLogger(__name__)


class OllamaGateway(BaseGateway, LLMProvider):
    """
    Gateway pour le serveur LLM local Ollama.
    
    Hérite de BaseGateway pour la gestion du client HTTP et le cycle de vie.
    Implémente l'interface LLMProvider pour une API LLM standardisée.
    
    Configuration :
        - OLLAMA_BASE_URL : URL de base pour le serveur Ollama (défaut: http://localhost:11434)
        - OLLAMA_MODEL : Nom du modèle à utiliser (défaut: qwen2.5:3b)
        - OLLAMA_TIMEOUT : Timeout de requête en secondes (défaut: 30)
    """
    
    def _get_required_config_keys(self) -> list[str]:
        """Variables d'environnement requises pour Ollama.
        
        Ollama fonctionne localement et toute la config a des valeurs par défaut sensées,
        donc aucune clé n'est strictement requise (contrairement aux APIs nécessitant des secrets).
        """
        return []
    
    def _load_config(self) -> Dict[str, Any]:
        """Charger la configuration spécifique à Ollama"""
        config = super()._load_config()
        
        # La génération LLM peut être lente (surtout les démarrages à froid) - donner assez de temps
        # mais n'essayer qu'une fois pour éviter les attentes cumulatives longues sur les timeouts répétés
        config["timeout"] = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        config["max_retries"] = 0  # Tentative unique, pas de réessais
        
        # Config spécifique Ollama
        config["OLLAMA_BASE_URL"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        config["OLLAMA_MODEL"] = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        
        return config
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Générer une complétion de chat via l'API Ollama.
        
        Args:
            messages: Liste de dicts de message [{"role": "system/user/assistant", "content": "..."}]
            temperature: Température d'échantillonnage
            max_tokens: Max tokens (note: Ollama utilise un nom de paramètre différent)
        
        Returns:
            Dict avec les clés : content, model, tokens, meta
        """
        # Vérifier si en mode mock (pas d'Ollama disponible)
        if self._is_mock:
            return self._generate_mock_response(messages, temperature)
        
        try:
            # Endpoint API chat Ollama
            url = f"{self._config['OLLAMA_BASE_URL']}/api/chat"
            
            # Préparer payload requête
            payload = {
                "model": self._config["OLLAMA_MODEL"],
                "messages": messages,
                "stream": False,  # Pas de streaming pour l'instant
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens  # Équivalent max_tokens pour Ollama
                }
            }
            
            # Faire la requête avec logique de réessai
            response = await self._retry_request(
                lambda: self._make_request("POST", url, json=payload)
            )
            
            # Extraire réponse
            content = response.get("message", {}).get("content", "")
            tokens = response.get("eval_count", 0)  # Compte de tokens
            
            return {
                "content": content,
                "model": self._config["OLLAMA_MODEL"],
                "tokens": tokens,
                "meta": {
                    "mock": False,
                    "provider": "ollama"
                }
            }
        
        except (GatewayTimeoutError, GatewayAPIError, GatewayError) as e:
            # Fallback vers mock si Ollama échoue
            logger.warning(f"La requête Ollama a échoué, repli vers mock : {e}")
            return self._generate_mock_response(
                messages, 
                temperature,
                reason="ollama_unreachable"
            )
        except Exception as e:
            logger.error(f"Erreur inattendue dans gateway Ollama : {e}")
            return self._generate_mock_response(
                messages,
                temperature,
                reason="unexpected_error"
            )
    
    def _generate_mock_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        reason: str = "ollama_unavailable"
    ) -> Dict[str, Any]:
        """
        Générer une réponse mock lorsque Ollama est indisponible.
        
        Args:
            messages: Messages originaux (pour mock contextuel)
            temperature: Température (inutilisée en mock)
            reason: Raison du mode mock
        
        Returns:
            Dict de réponse mock
        """
        # Extraire le message utilisateur pour un mocking contextuel
        user_message = next(
            (m["content"] for m in messages if m["role"] == "user"),
            ""
        )
        
        # Générer réponse mock contextuelle
        if "compar" in user_message.lower():
            mock_answer = (
                "**Mode Démo** - Ollama n'est pas disponible.\n\n"
                "Pour comparer ces offres, je recommanderais normalement d'analyser:\n"
                "- Le prix total\n"
                "- La durée du vol\n"
                "- Le nombre d'escales\n"
                "- La politique de bagages et de remboursement\n\n"
                "Veuillez démarrer Ollama pour obtenir une analyse détaillée."
            )
        elif "budget" in user_message.lower():
            mock_answer = (
                "**Mode Démo** - Ollama n'est pas disponible.\n\n"
                "Pour un conseil budgétaire, je suggérerais normalement 3 options:\n"
                "- Économique: Privilégier le prix minimal\n"
                "- Équilibré: Compromis prix/confort\n"
                "- Confort: Priorité au temps et qualité\n\n"
                "Veuillez démarrer Ollama pour des recommandations personnalisées."
            )
        else:
            mock_answer = (
                "**Mode Démo** - Ollama n'est pas disponible.\n\n"
                "Je suis un assistant IA qui vous aide dans vos décisions de voyage. "
                "Pour obtenir des réponses personnalisées, veuillez configurer et démarrer Ollama.\n\n"
                "Commandes:\n"
                "- `ollama serve` (démarrer le serveur)\n"
                "- `ollama pull qwen2.5:3b` (télécharger le modèle)"
            )
        
        return {
            "content": mock_answer,
            "model": "mock-ollama",
            "tokens": len(mock_answer.split()),  # Estimation grossière
            "meta": {
                "mock": True,
                "reason": reason,
                "provider": "ollama"
            }
        }
