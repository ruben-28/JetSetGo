"""
Travel Gateway Module
Handles all external travel API calls (flights, hotels, offers).
Supports mock mode when TRAVEL_API_KEY is not configured.
"""

from typing import List, Dict, Optional
import random
from .base_gateway import BaseGateway


class TravelGateway(BaseGateway):
    """
    Gateway for travel API integration.
    
    Responsibilities:
    - Search flights from external travel APIs
    - Retrieve offer details
    - Return mock data when API key is not configured
    
    Mock Mode:
    - Activated when TRAVEL_API_KEY is missing
    - Returns deterministic fake data for testing
    """
    
    def _get_required_config_keys(self) -> list[str]:
        """Required configuration keys for travel API"""
        return ["TRAVEL_API_KEY", "TRAVEL_API_BASE_URL"]
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> List[Dict]:
        """
        Search for flight offers.
        
        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional for one-way
            adults: Number of adult passengers
        
        Returns:
            List of flight offers (sorted by price)
        
        Mock Mode:
            Returns 10 fake offers with realistic data
        """
        if self.is_mock_mode():
            return await self._mock_search_flights(
                origin, destination, depart_date, return_date, adults
            )
        
        # Real API call (to be implemented when API is available)
        return await self._real_search_flights(
            origin, destination, depart_date, return_date, adults
        )
    
    async def get_offer_details(self, offer_id: str) -> Dict:
        """
        Get detailed information about a specific offer.
        
        Args:
            offer_id: Unique offer identifier
        
        Returns:
            Offer details (baggage, refund policy, etc.)
        
        Mock Mode:
            Returns fake details based on offer_id
        """
        if self.is_mock_mode():
            return await self._mock_get_details(offer_id)
        
        # Real API call (to be implemented)
        return await self._real_get_details(offer_id)
    
    # ========================================================================
    # Mock Mode Implementation
    # ========================================================================
    
    async def _mock_search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str],
        adults: int
    ) -> List[Dict]:
        """Generate mock flight data (deterministic based on inputs)"""
        # Use seed for consistent results per search
        seed_str = f"{origin}-{destination}-{depart_date}-{return_date}-{adults}"
        random.seed(seed_str)
        
        airlines = ["ElAl", "Air France", "Lufthansa", "Ryanair", "Turkish Airlines"]
        offers = []
        
        base_price = 300
        for i in range(10):
            price = base_price + random.randint(-40, 250)
            duration = random.randint(180, 720)  # minutes
            stops = random.choice([0, 0, 1, 1, 2])
            
            offer_id = f"{origin[:3].upper()}-{destination[:3].upper()}-{depart_date.replace('-','')}-{i}"
            
            offers.append({
                "id": offer_id,
                "departure": origin,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date or "",
                "airline": random.choice(airlines),
                "price": max(50, price),
                "duration_min": duration,
                "stops": stops,
                "score": round(random.uniform(3.2, 4.9), 1),
                "adults": adults,
                "mock": True
            })
        
        # Sort by price
        offers.sort(key=lambda x: x["price"])
        return offers
    
    async def _mock_get_details(self, offer_id: str) -> Dict:
        """Generate mock offer details"""
        return {
            "id": offer_id,
            "baggage": "Cabin bag + 20kg checked baggage",
            "refund_policy": "Partial refund available up to 48h before departure",
            "notes": "Mock offer for testing. Replace with real API later.",
            "hotel_suggestion": {
                "name": "City Center Hotel",
                "stars": 4,
                "night_price": 120
            },
            "mock": True
        }
    
    # ========================================================================
    # Real API Implementation (Placeholder)
    # ========================================================================
    
    async def _real_search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str],
        adults: int
    ) -> List[Dict]:
        """
        Real API implementation (to be completed when API is available).
        
        Example implementation:
            url = f"{self._get_config('TRAVEL_API_BASE_URL')}/search"
            params = {
                "origin": origin,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
                "adults": adults
            }
            headers = {
                "Authorization": f"Bearer {self._get_config('TRAVEL_API_KEY')}"
            }
            
            response = await self._retry_request(
                lambda: self._make_request("GET", url, params=params, headers=headers)
            )
            
            return response.get("offers", [])
        """
        self.logger.warning("Real API not implemented yet, using mock data")
        return await self._mock_search_flights(origin, destination, depart_date, return_date, adults)
    
    async def _real_get_details(self, offer_id: str) -> Dict:
        """Real API implementation for offer details (placeholder)"""
        self.logger.warning("Real API not implemented yet, using mock data")
        return await self._mock_get_details(offer_id)
