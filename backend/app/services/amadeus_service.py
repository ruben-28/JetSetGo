"""
Module de Service Amadeus
Service d'intégration avec l'API Amadeus.
Responsabilités:
- Authentification (OAuth2 Client Credentials).
- Récupération des données référentielles (Compagnies aériennes).
- Gestion du cache simple pour les compagnies.
"""

import os
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AmadeusService:
    """
    Service pour interagir avec l'API Amadeus (Vols, Compagnies).
    """
    
    BASE_URL = "https://test.api.amadeus.com"
    TOKEN_URL = f"{BASE_URL}/v1/security/oauth2/token"
    AIRLINE_URL = f"{BASE_URL}/v1/reference-data/airlines"
    
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._airline_cache: Dict[str, Dict[str, Any]] = {}
        
        if not self.client_id or not self.client_secret:
            logger.warning("AMADEUS_CLIENT_ID ou AMADEUS_CLIENT_SECRET non définis dans l'environnement.")

    async def _get_access_token(self) -> str:
        """
        Récupère un token d'accès auprès d'Amadeus (Client Credentials).
        Renouvelle automatiquement le token s'il est expiré ou inexistant.
        """
        # Retourne le token existant s'il est encore valide
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                data = response.json()
                
                self._access_token = data["access_token"]
                # L'expiration est en secondes. On retire 60s par sécurité.
                expires_in = int(data.get("expires_in", 1799))
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Échec obtention token Amadeus : {e.response.text}")
                raise ValueError(f"Authentification échouée : {e.response.text}")
            except Exception as e:
                logger.error(f"Erreur obtention token Amadeus : {e}")
                raise

    async def get_airline_by_code(self, iata_code: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une compagnie aérienne par son code IATA.
        
        Args:
            iata_code: Code IATA à 2 caractères (ex: 'AF').
            
        Returns:
            Dictionnaire contenant les détails de la compagnie.
            
        Raises:
            ValueError: Si le code est invalide ou non trouvé.
        """
        if not iata_code or len(iata_code) != 2:
             raise ValueError(f"Format code IATA invalide : '{iata_code}'. Doit faire 2 caractères.")

        # Vérification du cache mémoire en premier
        if iata_code in self._airline_cache:
            return self._airline_cache[iata_code]

        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.AIRLINE_URL,
                    params={"airlineCodes": iata_code},
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                # Vérifie 404 ou données vides
                if response.status_code == 404:
                     raise ValueError(f"Compagnie avec code '{iata_code}' introuvable.")
                     
                response.raise_for_status()
                data = response.json()
                
                if "data" not in data or not data["data"]:
                     raise ValueError(f"Compagnie avec code '{iata_code}' introuvable (résultat vide).")
                     
                result = data["data"][0]
                
                # Mise en cache
                self._airline_cache[iata_code] = result
                
                return result
                
            except httpx.HTTPStatusError as e:
                # L'API retourne 400/404 pour les codes invalides
                try:
                    error_data = e.response.json()
                    errors = error_data.get("errors", [])
                    if errors:
                        detail = errors[0].get("detail") or errors[0].get("title")
                        raise ValueError(f"Erreur API Amadeus : {detail}")
                except ValueError:
                    pass
                
                raise ValueError(f"Erreur HTTP récupération compagnie : {e}")
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                logger.error(f"Erreur récupération compagnie {iata_code} : {e}")
                raise ValueError(f"Erreur système : {str(e)}")
