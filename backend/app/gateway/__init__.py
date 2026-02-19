"""
Gateway Module
Exports all gateway classes for external API integration.
"""

from .base_gateway import (
    BaseGateway,
    GatewayError,
    GatewayConfigError,
    GatewayTimeoutError,
    GatewayAPIError
)
from .travel_provider import TravelProvider
from .huggingface_gateway import HuggingFaceGateway
from .llm_provider import LLMProvider
from .ollama_gateway import OllamaGateway
from .openai_provider import OpenAIProvider

# Alias for backward compatibility
HFGateway = HuggingFaceGateway

__all__ = [
    # Base classes
    "BaseGateway",
    "LLMProvider",
    
    # Exceptions
    "GatewayError",
    "GatewayConfigError",
    "GatewayTimeoutError",
    "GatewayAPIError",
    
    # Gateway implementations
    "TravelGateway",
    "HuggingFaceGateway",
    "HFGateway",  # Export alias
    "OllamaGateway",
    "OpenAIProvider",
]

