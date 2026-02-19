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
<<<<<<< HEAD
    "TravelProvider",
    "HFGateway",
=======
    "HuggingFaceGateway",
    "HFGateway",  # Export alias
>>>>>>> c1dbc83ffe7cd2825c0c5f8e87713612e61ac51b
    "OllamaGateway",
    "OpenAIProvider",
]

# Alias for consistent naming
TravelGateway = TravelProvider

