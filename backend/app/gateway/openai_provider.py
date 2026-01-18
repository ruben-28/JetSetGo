"""
OpenAI Provider (Placeholder)
Future implementation for OpenAI/ChatGPT API.
"""

from typing import Dict, Any, List
from .llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    Placeholder for OpenAI provider implementation.
    
    Future implementation will use OpenAI's Chat Completions API.
    
    Configuration (when implemented):
        - OPENAI_API_KEY: OpenAI API key
        - OPENAI_MODEL: Model name (e.g., gpt-4o-mini, gpt-4)
        - OPENAI_TIMEOUT: Request timeout in seconds
    """
    
    def __init__(self):
        """Initialize placeholder provider"""
        pass
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Placeholder for OpenAI chat completion.
        
        To implement:
        1. Install openai package: pip install openai
        2. Use openai.AsyncOpenAI client
        3. Call client.chat.completions.create()
        4. Handle rate limits and errors
        5. Return standardized response format
        """
        raise NotImplementedError(
            "OpenAI provider not yet implemented. "
            "Use LLM_PROVIDER=ollama in environment variables."
        )
    
    def is_mock_mode(self) -> bool:
        """OpenAI provider is always 'mock' until implemented"""
        return True
