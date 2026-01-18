"""
DTOs (Data Transfer Objects) for AI Context
Stable data structures synchronized with backend schemas.
"""

from typing import Optional


class OfferDTO:
    """DTO for flight offer context - must match backend OfferDTO"""
    
    def __init__(
        self,
        id: str,
        price: float,
        currency: str,
        airline: str,
        departure: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str],
        duration_min: int,
        stops: int,
        baggage: Optional[str] = None,
        refund_policy: Optional[str] = None
    ):
        self.id = id
        self.price = price
        self.currency = currency
        self.airline = airline
        self.departure = departure
        self.destination = destination
        self.depart_date = depart_date
        self.return_date = return_date
        self.duration_min = duration_min
        self.stops = stops
        self.baggage = baggage
        self.refund_policy = refund_policy
    
    def to_dict(self):
        """Convert to dict for JSON serialization"""
        return {
            "id": self.id,
            "price": self.price,
            "currency": self.currency,
            "airline": self.airline,
            "departure": self.departure,
            "destination": self.destination,
            "depart_date": self.depart_date,
            "return_date": self.return_date,
            "duration_min": self.duration_min,
            "stops": self.stops,
            "baggage": self.baggage,
            "refund_policy": self.refund_policy
        }


class BookingDTO:
    """DTO for booking context - must match backend BookingDTO"""
    
    def __init__(
        self,
        booking_id: str,
        offer_id: str,
        status: str,
        user_id: Optional[int],
        created_at: str,
        price: float,
        adults: int
    ):
        self.booking_id = booking_id
        self.offer_id = offer_id
        self.status = status
        self.user_id = user_id
        self.created_at = created_at
        self.price = price
        self.adults = adults
    
    def to_dict(self):
        """Convert to dict for JSON serialization"""
        return {
            "booking_id": self.booking_id,
            "offer_id": self.offer_id,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "price": self.price,
            "adults": self.adults
        }
