"""
Provider OpenAI (Placeholder)
Implémentation future pour l'API OpenAI/ChatGPT.
"""

from typing import Dict, Any, List
from .llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    Placeholder pour l'implémentation du fournisseur OpenAI.
    
    L'implémentation future utilisera l'API Chat Completions d'OpenAI.
    
    Configuration (une fois implémentée) :
        - OPENAI_API_KEY : Clé API OpenAI
        - OPENAI_MODEL : Nom du modèle (ex: gpt-4o-mini, gpt-4)
        - OPENAI_TIMEOUT : Timeout de requête en secondes
    """
    
    def __init__(self):
        """Initialiser le provider placeholder"""
        pass
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Placeholder pour la complétion de chat OpenAI.
        
        À implémenter :
        1. Installer le package openai : pip install openai
        2. Utiliser le client openai.AsyncOpenAI
        3. Appeler client.chat.completions.create()
        4. Gérer les limites de débit et les erreurs
        5. Retourner le format de réponse standardisé
        """
        raise NotImplementedError(
            "Le fournisseur OpenAI n'est pas encore implémenté. "
            "Utilisez LLM_PROVIDER=ollama dans les variables d'environnement."
        )
    
    def is_mock_mode(self) -> bool:
        """Le fournisseur OpenAI est toujours en 'mock' jusqu'à son implémentation"""
        return True
