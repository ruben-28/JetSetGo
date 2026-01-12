"""
Travel Service Module (DEPRECATED - Facade for CQRS)

This module is maintained for backward compatibility only.
All business logic has been moved to CQRS handlers:
- FlightQueries (app.cqrs.queries.flight_queries) for read operations
- BookingCommands (app.cqrs.commands.booking_commands) for write operations

Usage:
    Prefer using CQRS handlers directly:
        from app.cqrs import FlightQueries, BookingCommands
    
    This service is a thin facade that delegates to CQRS handlers.
"""

from typing import List, Dict, Optional
from app.gateway import TravelGateway
from app.cqrs import FlightQueries


class TravelService:
    """
    Service layer for travel operations (DEPRECATED).
    
    This class is maintained for backward compatibility.
    It acts as a facade that delegates all operations to CQRS handlers.
    
    Migration Guide:
    - For reads: Use FlightQueries directly
    - For writes: Use BookingCommands directly
    
    Deprecated: Will be removed in future versions.
    """
    
    def __init__(self, gateway: TravelGateway):
        """
        Initialize service with gateway dependency.
        
        Args:
            gateway: TravelGateway instance for external API calls
        """
        self.gateway = gateway
        # Create CQRS query handler
        self._queries = FlightQueries(gateway)
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        budget: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for flight offers (delegates to FlightQueries).
        
        DEPRECATED: Use FlightQueries.search_flights() directly.
        
        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional
            adults: Number of adult passengers
            budget: Maximum budget (optional)
        
        Returns:
            List of flight offers (filtered and sorted)
        """
        # Delegate to CQRS query handler
        return await self._queries.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            budget=budget
        )
    
    async def get_offer_details(self, offer_id: str) -> Dict:
        """
        Get detailed information about a specific offer (delegates to FlightQueries).
        
        DEPRECATED: Use FlightQueries.get_offer_details() directly.
        
        Args:
            offer_id: Unique offer identifier
        
        Returns:
            Offer details
        """
        # Delegate to CQRS query handler
        return await self._queries.get_offer_details(offer_id)
