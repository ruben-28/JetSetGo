"""
LLM Provider Interface
Abstract base class for all LLM providers (Ollama, OpenAI, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent API across different backends (Ollama, OpenAI, Anthropic, etc.)
    """
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate chat completion from messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
                     Example: [{"role": "system", "content": "..."}, 
                              {"role": "user", "content": "..."}]
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Dict containing:
                - content: str - Generated response text
                - model: str - Model name used
                - tokens: int - Token count (if available)
                - meta: dict - Additional metadata including 'mock' flag
        
        Raises:
            GatewayError: On provider errors
            GatewayTimeoutError: On timeout
        """
        pass
    
    @abstractmethod
    def is_mock_mode(self) -> bool:
        """
        Check if provider is running in mock mode.
        
        Returns:
            True if mock mode (provider unavailable), False otherwise
        """
        pass
