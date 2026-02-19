"""
Module de Gateway de Base (Base Gateway)
Fournit une classe de base abstraite pour toutes les gateways API externes avec :
- Client HTTP asynchrone (httpx)
- Gestion de configuration (variables d'environnement)
- Logique de réessai avec backoff exponentiel
- Gestion personnalisée des exceptions
- Détection du mode Mock
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
from asyncio import sleep


# ============================================================================
# Exceptions Personnalisées
# ============================================================================

class GatewayError(Exception):
    """Exception de base pour toutes les erreurs de gateway"""
    pass


class GatewayConfigError(GatewayError):
    """Levée lorsque la configuration du gateway est invalide ou manquante"""
    pass


class GatewayTimeoutError(GatewayError):
    """Levée lorsque la requête du gateway expire (timeout)"""
    pass


class GatewayAPIError(GatewayError):
    """Levée lorsque l'API externe retourne une erreur"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ============================================================================
# Gateway de Base
# ============================================================================

class BaseGateway(ABC):
    """
    Classe de base abstraite pour toutes les gateways API.
    
    Responsabilités :
    - Gérer le cycle de vie de httpx.AsyncClient
    - Charger la configuration depuis les variables d'environnement
    - Implémenter la logique de réessai avec backoff exponentiel
    - Fournir la détection du mode Mock
    - Gérer les erreurs HTTP courantes
    
    Les sous-classes doivent implémenter :
    - _get_required_config_keys() : Liste des clés de var d'env requises
    """
    
    def __init__(self):
        """Initialise le gateway avec la configuration et le client HTTP"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client: Optional[httpx.AsyncClient] = None
        self._config = self._load_config()
        self._is_mock = self._detect_mock_mode()
        
        if self._is_mock:
            self.logger.warning(f"{self.__class__.__name__} exécution en MODE MOCK (clés API manquantes)")
    
    # ========================================================================
    # Gestion de la Configuration
    # ========================================================================
    
    def _load_config(self) -> Dict[str, Any]:
        """Charger la configuration depuis les variables d'environnement"""
        config = {
            "timeout": int(os.getenv("GATEWAY_TIMEOUT", "30")),
            "max_retries": int(os.getenv("GATEWAY_MAX_RETRIES", "3")),
            "retry_delay": float(os.getenv("GATEWAY_RETRY_DELAY", "1.0")),
        }
        
        # Charger la config spécifique au gateway
        for key in self._get_required_config_keys():
            config[key] = os.getenv(key)
        
        return config
    
    @abstractmethod
    def _get_required_config_keys(self) -> list[str]:
        """
        Retourne la liste des clés de variables d'environnement requises.
        Les sous-classes doivent implémenter ceci.
        
        Exemple :
            return ["TRAVEL_API_KEY", "TRAVEL_API_BASE_URL"]
        """
        pass
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """Obtenir une valeur de configuration par clé"""
        return self._config.get(key, default)
    
    def _detect_mock_mode(self) -> bool:
        """
        Détecte si le gateway doit s'exécuter en mode mock.
        Retourne True si une clé API requise est manquante.
        """
        required_keys = self._get_required_config_keys()
        for key in required_keys:
            if not self._config.get(key):
                return True
        return False
    
    def is_mock_mode(self) -> bool:
        """Vérifie si le gateway est en mode mock"""
        return self._is_mock
    
    # ========================================================================
    # Gestion du Client HTTP (avec nettoyage approprié)
    # ========================================================================
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtenir ou créer le client HTTP asynchrone"""
        if self._client is None:
            timeout = httpx.Timeout(self._config["timeout"])
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client
    
    async def close(self):
        """Fermer le client HTTP (nettoyage) - IMPORTANT : Appeler ceci pour éviter les fuites de ressources"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Entrée du context manager asynchrone"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Sortie du context manager asynchrone - ferme automatiquement le client"""
        await self.close()
        return False
    
    # ========================================================================
    # Méthodes de Requête HTTP
    # ========================================================================
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Effectuer une requête HTTP avec gestion des erreurs.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour la requête httpx
        
        Returns:
            JSON de réponse sous forme de dict
        
        Raises:
            GatewayTimeoutError: En cas de timeout
            GatewayAPIError: En cas d'erreur de réponse API
            GatewayError: Pour les autres erreurs
        """
        client = await self._get_client()
        
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        
        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout de la requête : {url}")
            raise GatewayTimeoutError(f"La requête a expiré : {url}") from e
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Erreur HTTP {e.response.status_code} : {url}")
            raise GatewayAPIError(
                f"L'API a retourné une erreur : {e.response.status_code}",
                status_code=e.response.status_code
            ) from e
        
        except Exception as e:
            self.logger.error(f"Erreur inattendue : {e}")
            raise GatewayError(f"Échec de la requête : {str(e)}") from e
    
    async def _retry_request(
        self,
        request_func,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Exécuter une requête avec logique de réessai (backoff exponentiel).
        
        Args:
            request_func: Fonction asynchrone qui effectue la requête
            max_retries: Tentatives max (utilise le défaut de la config si None)
        
        Returns:
            JSON de réponse sous forme de dict
        
        Raises:
            GatewayError: Après épuisement de tous les réessais
        """
        # Utiliser le défaut de config si max_retries est None (0 explicite doit être respecté)
        if max_retries is None:
            max_retries = self._config["max_retries"]
        retry_delay = self._config["retry_delay"]
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await request_func()
            
            except GatewayTimeoutError as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # Backoff exponentiel
                    self.logger.warning(f"Réessai {attempt + 1}/{max_retries} après {wait_time}s")
                    await sleep(wait_time)
                else:
                    self.logger.error(f"Tous les réessais sont épuisés")
            
            except GatewayAPIError as e:
                # Ne pas réessayer sur les erreurs 4xx (erreurs client)
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                
                last_exception = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.warning(f"Réessai {attempt + 1}/{max_retries} après {wait_time}s")
                    await sleep(wait_time)
                else:
                    self.logger.error(f"Tous les réessais sont épuisés")
        
        # Tous les réessais épuisés
        raise last_exception or GatewayError("La requête a échoué après réessais")
    
    # ========================================================================
    # Méthodes Utilitaires
    # ========================================================================
    
    def __repr__(self) -> str:
        mode = "MOCK" if self._is_mock else "LIVE"
        return f"<{self.__class__.__name__} mode={mode}>"
