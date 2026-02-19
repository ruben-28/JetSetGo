"""
Interface Provider LLM
Classe de base abstraite pour tous les fournisseurs LLM (Ollama, OpenAI, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMProvider(ABC):
    """
    Interface abstraite pour les fournisseurs LLM.
    
    Tous les fournisseurs LLM doivent implémenter cette interface pour assurer
    une API cohérente à travers différents backends (Ollama, OpenAI, Anthropic, etc.)
    """
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Générer une complétion de chat à partir des messages.
        
        Args:
            messages: Liste de dicts de message avec clés 'role' et 'content'
                     Exemple : [{"role": "system", "content": "..."}, 
                              {"role": "user", "content": "..."}]
            temperature: Température d'échantillonnage (0-1)
            max_tokens: Maximum de tokens à générer
        
        Returns:
            Dict contenant :
                - content: str - Texte de réponse généré
                - model: str - Nom du modèle utilisé
                - tokens: int - Compte de tokens (si disponible)
                - meta: dict - Métadonnées supplémentaires incluant le flag 'mock'
        
        Raises:
            GatewayError: Sur erreurs du fournisseur
            GatewayTimeoutError: Sur timeout
        """
        pass
    
    @abstractmethod
    def is_mock_mode(self) -> bool:
        """
        Vérifier si le fournisseur s'exécute en mode mock.
        
        Returns:
            True si mode mock (fournisseur indisponible), False sinon
        """
        pass
