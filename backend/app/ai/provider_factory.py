"""
Provider Factory Module
Factory function to create the appropriate LLM provider based on configuration.
"""

import os
import logging
from app.gateway import OllamaGateway, OpenAIProvider, LLMProvider


logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    """
    Factory pour obtenir le LLM provider configuré.
    
    Lit LLM_PROVIDER env var et retourne:
    - OllamaGateway si "ollama" (default)
    - OpenAIProvider si "openai" (placeholder, pas encore implémenté)
    
    Log warnings si mode mock détecté.
    
    Returns:
        LLMProvider instance configured from environment
    """
    provider_type = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider_type == "ollama":
        gateway = OllamaGateway()
        if gateway.is_mock_mode():
            logger.warning(
                "⚠️  Ollama gateway running in MOCK MODE - "
                "check OLLAMA_BASE_URL and model availability. "
                "Start Ollama with: ollama serve && ollama pull qwen2.5:3b"
            )
        return gateway
    
    elif provider_type == "openai":
        # Future implementation
        provider = OpenAIProvider()
        logger.warning(
            "⚠️  OpenAI provider not yet fully implemented. "
            "Using placeholder that will raise NotImplementedError. "
            "Use LLM_PROVIDER=ollama instead."
        )
        return provider
    
    else:
        logger.error(
            f"Unknown LLM_PROVIDER: {provider_type}. "
            f"Valid options: 'ollama', 'openai'. Falling back to Ollama."
        )
        return OllamaGateway()
