"""
Flight Queries Module
Query handler for flight search operations (read-only, CQRS Query side).

This module handles all READ operations for flights. It does NOT modify
any state in the system - it only retrieves and returns data.
"""

from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException

from app.gateway import TravelGateway


class FlightQueries:
    """
    Query handler for flight-related read operations.
    
    CQRS Query Side - Responsibilities:
    - Search flights (read-only)
    - Get offer details (read-only)
    - Validate query parameters
    - Apply read-side business rules (filtering, sorting)
    - NO STATE MODIFICATION
    
    This class focuses purely on data retrieval and query optimization.
    """
    
    def __init__(self, gateway: TravelGateway):
        """
        Initialize query handler with gateway dependency.
        
        Args:
            gateway: TravelGateway instance for external API calls
        """
        self.gateway = gateway
    
    # ========================================================================
    # Public Query Methods
    # ========================================================================
    
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
        Search for flight offers (READ operation).
        
        Query flow:
        1. Validate query parameters
        2. Fetch data from gateway
        3. Apply filters (budget)
        4. Sort results
        5. Return data
        
        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD), optional
            adults: Number of adult passengers
            budget: Maximum budget (optional filter)
        
        Returns:
            List of flight offers (filtered and sorted)
        
        Raises:
            HTTPException: On validation errors
        """
        # 1. Validate inputs
        self._validate_dates(depart_date, return_date)
        self._validate_adults(adults)
        self._validate_budget(budget)
        
        # 2. Fetch data from gateway
        offers = await self.gateway.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults
        )
        
        # 3. Apply business rules (read-side filters)
        if budget:
            offers = self._filter_by_budget(offers, budget)
        
        # 4. Sort by price
        offers = self._sort_by_price(offers)
        
        return offers
    
    async def get_offer_details(self, offer_id: str) -> Dict:
        """
        Get detailed information about a specific offer (READ operation).
        
        Args:
            offer_id: Unique offer identifier
        
        Returns:
            Offer details
        
        Raises:
            HTTPException: On validation errors
        """
        # 1. Validate offer_id
        if not offer_id or len(offer_id) < 5:
            raise HTTPException(
                status_code=400,
                detail="Invalid offer_id format"
            )
        
        # 2. Fetch details from gateway
        details = await self.gateway.get_offer_details(offer_id)
        
        return details
    
    # ========================================================================
    # Validation Logic (Query Side)
    # ========================================================================
    
    def _validate_dates(self, depart_date: str, return_date: Optional[str]):
        """
        Validate departure and return dates.
        
        Rules:
        - Dates must be in YYYY-MM-DD format
        - Departure date must be in the future
        - Return date must be after departure date (if provided)
        """
        try:
            depart = datetime.strptime(depart_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid depart_date format. Use YYYY-MM-DD"
            )
        
        # Check if departure is in the future
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if depart < today:
            raise HTTPException(
                status_code=400,
                detail="Departure date must be in the future"
            )
        
        # Validate return date if provided
        if return_date:
            try:
                return_dt = datetime.strptime(return_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid return_date format. Use YYYY-MM-DD"
                )
            
            if return_dt <= depart:
                raise HTTPException(
                    status_code=400,
                    detail="Return date must be after departure date"
                )
    
    def _validate_adults(self, adults: int):
        """Validate number of adults"""
        if adults < 1 or adults > 9:
            raise HTTPException(
                status_code=400,
                detail="Number of adults must be between 1 and 9"
            )
    
    def _validate_budget(self, budget: Optional[int]):
        """Validate budget if provided"""
        if budget is not None and budget < 0:
            raise HTTPException(
                status_code=400,
                detail="Budget must be a positive number"
            )
    
    # ========================================================================
    # Read-Side Business Rules
    # ========================================================================
    
    def _filter_by_budget(self, offers: List[Dict], budget: int) -> List[Dict]:
        """Filter offers by maximum budget"""
        return [offer for offer in offers if offer["price"] <= budget]
    
    def _sort_by_price(self, offers: List[Dict]) -> List[Dict]:
        """Sort offers by price (ascending)"""
        return sorted(offers, key=lambda x: x["price"])
    
    # ========================================================================
    # User Bookings Query (Read Model)
    # ========================================================================
    
    async def get_user_bookings(self, user_id: int) -> List[Dict]:
        """
        Get all bookings for a specific user (READ operation from Read Model).
        
        Args:
            user_id: User ID to fetch bookings for
        
        Returns:
            List of booking records for the user
        """
        from app.auth.db import SessionLocal
        from app.auth.models import Booking
        
        session = SessionLocal()
        try:
            bookings = (
                session.query(Booking)
                .filter(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
                .all()
            )
            
            return [
                {
                    "id": b.id,
                    "offer_id": b.offer_id,
                    "departure": b.departure,
                    "destination": b.destination,
                    "depart_date": b.depart_date,
                    "return_date": b.return_date,
                    "price": b.price,
                    "adults": b.adults,
                    "status": b.status,
                    "created_at": b.created_at.isoformat() if b.created_at else None
                }
                for b in bookings
            ]
        finally:
            session.close()

