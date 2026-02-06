import os
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AmadeusService:
    """
    Service to interact with the Amadeus API for airline information.
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
            logger.warning("AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET not set in environment variables.")

    async def _get_access_token(self) -> str:
        """
        Retrieves an access token from Amadeus using Client Credentials grant.
        Auto-refreshes if expired or not exists.
        """
        # Return existing valid token
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
                # Expires in is in seconds. Remove a buffer of 60s to be safe.
                expires_in = int(data.get("expires_in", 1799))
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
                
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get Amadeus token: {e.response.text}")
                raise ValueError(f"Authentication failed: {e.response.text}")
            except Exception as e:
                logger.error(f"Error getting Amadeus token: {e}")
                raise

    async def get_airline_by_code(self, iata_code: str) -> Dict[str, Any]:
        """
        Retrieves airline details by IATA code.
        
        Args:
            iata_code: The 2-character IATA airline code (e.g. 'AF').
            
        Returns:
            Dictionary containing airline details.
            
        Raises:
            ValueError: If code is invalid or not found.
        """
        if not iata_code or len(iata_code) != 2:
             raise ValueError(f"Invalid IATA code format: '{iata_code}'. Must be 2 characters.")

        # Check in-memory cache first
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
                
                # Check for 404 or empty data (Amadeus might return 200 with warnings for not found)
                if response.status_code == 404:
                     raise ValueError(f"Airline with code '{iata_code}' not found.")
                     
                response.raise_for_status()
                data = response.json()
                
                if "data" not in data or not data["data"]:
                     # Sometimes API returns 200 but data is empty if not found in specific context
                     raise ValueError(f"Airline with code '{iata_code}' not found (empty result).")
                     
                result = data["data"][0]
                
                # Cache the result
                self._airline_cache[iata_code] = result
                
                return result
                
            except httpx.HTTPStatusError as e:
                # API returns 400/404 for invalid/unknown codes usually in a structured JSON error
                # We try to extract a useful message
                try:
                    error_data = e.response.json()
                    errors = error_data.get("errors", [])
                    if errors:
                        detail = errors[0].get("detail") or errors[0].get("title")
                        raise ValueError(f"Amadeus API Error: {detail}")
                except ValueError:
                    # re-raise original if it wasn't the JSON we expected
                    pass
                
                raise ValueError(f"HTTP Error fetching airline: {e}")
            except Exception as e:
                 # If it is already our ValueError, just re-raise
                if isinstance(e, ValueError):
                    raise
                logger.error(f"Error fetching airline {iata_code}: {e}")
                raise ValueError(f"System error: {str(e)}")
