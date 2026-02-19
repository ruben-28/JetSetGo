"""
Module Factory de Provider
Fonction Factory pour créer le fournisseur LLM approprié basé sur la configuration.
"""

import os
import logging
from app.gateway import OllamaGateway, OpenAIProvider, LLMProvider


logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """
    Factory pour obtenir le fournisseur LLM configuré.
    
    Lit la variable LLM_PROVIDER et retourne :
    - OllamaGateway si "ollama" (défaut)
    - OpenAIProvider si "openai" (placeholder, pas encore implémenté)
    
    Log des avertissements si le mode mock est détecté.
    
    Retourne :
        Instance de LLMProvider configurée depuis l'environnement
    """
    provider_type = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider_type == "ollama":
        gateway = OllamaGateway()
        if gateway.is_mock_mode():
            logger.warning(
                "⚠️  Ollama gateway s'exécute en MODE MOCK - "
                "vérifiez OLLAMA_BASE_URL et la disponibilité du modèle. "
                "Démarrez Ollama avec : ollama serve && ollama pull qwen2.5:3b"
            )
        return gateway
    
    elif provider_type == "openai":
        # Implémentation future
        provider = OpenAIProvider()
        logger.warning(
            "⚠️  Le fournisseur OpenAI n'est pas encore totalement implémenté. "
            "Utilisation du placeholder qui lèvera NotImplementedError. "
            "Utilisez LLM_PROVIDER=ollama à la place."
        )
        return provider
    
    else:
        logger.error(
            f"LLM_PROVIDER inconnu : {provider_type}. "
            f"Options valides : 'ollama', 'openai'. Repli sur Ollama."
        )
        return OllamaGateway()
