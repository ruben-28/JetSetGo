"""
Ollama Gateway
LLM provider implementation for local Ollama server.
"""

import os
import logging
from typing import Dict, Any, List, Optional

from .base_gateway import BaseGateway, GatewayError, GatewayTimeoutError, GatewayAPIError
from .llm_provider import LLMProvider


logger = logging.getLogger(__name__)


class OllamaGateway(BaseGateway, LLMProvider):
    """
    Gateway for Ollama local LLM server.
    
    Inherits from BaseGateway for HTTP client management and lifecycle.
    Implements LLMProvider interface for standardized LLM API.
    
    Configuration:
        - OLLAMA_BASE_URL: Base URL for Ollama server (default: http://localhost:11434)
        - OLLAMA_MODEL: Model name to use (default: qwen2.5:3b)
        - OLLAMA_TIMEOUT: Request timeout in seconds (default: 30)
    """
    
    def _get_required_config_keys(self) -> list[str]:
        """Required environment variables for Ollama"""
        return ["OLLAMA_BASE_URL", "OLLAMA_MODEL"]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama-specific configuration"""
        config = super()._load_config()
        
        # Override timeout for LLM requests (longer than default)
        config["timeout"] = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        
        # Ollama-specific config
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
        Generate chat completion via Ollama API.
        
        Args:
            messages: List of message dicts [{"role": "system/user/assistant", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Max tokens (note: Ollama uses different param name)
        
        Returns:
            Dict with keys: content, model, tokens, meta
        """
        # Check if in mock mode (no Ollama available)
        if self._is_mock:
            return self._generate_mock_response(messages, temperature)
        
        try:
            # Ollama chat API endpoint
            url = f"{self._config['OLLAMA_BASE_URL']}/api/chat"
            
            # Prepare request payload
            payload = {
                "model": self._config["OLLAMA_MODEL"],
                "messages": messages,
                "stream": False,  # No streaming for now
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens  # Ollama's max_tokens equivalent
                }
            }
            
            # Make request with retry logic
            response = await self._retry_request(
                lambda: self._make_request("POST", url, json=payload)
            )
            
            # Extract response
            content = response.get("message", {}).get("content", "")
            tokens = response.get("eval_count", 0)  # Token count
            
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
            # Fallback to mock if Ollama fails
            logger.warning(f"Ollama request failed, falling back to mock: {e}")
            return self._generate_mock_response(
                messages, 
                temperature,
                reason="ollama_unreachable"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Ollama gateway: {e}")
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
        Generate mock response when Ollama is unavailable.
        
        Args:
            messages: Original messages (for context-aware mock)
            temperature: Temperature (unused in mock)
            reason: Reason for mock mode
        
        Returns:
            Mock response dict
        """
        # Extract user message for context-aware mocking
        user_message = next(
            (m["content"] for m in messages if m["role"] == "user"),
            ""
        )
        
        # Generate context-aware mock response
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
            "tokens": len(mock_answer.split()),  # Rough estimate
            "meta": {
                "mock": True,
                "reason": reason,
                "provider": "ollama"
            }
        }
