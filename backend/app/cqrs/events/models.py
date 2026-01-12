"""
Event Models for Event Sourcing
Defines all domain events that capture state changes in the system.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class BaseEvent(BaseModel):
    """
    Base class for all domain events.
    
    All events in the system inherit from this base class to ensure
    consistent structure and traceability.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aggregate_id: str  # ID of the entity this event relates to (e.g., booking_id)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FlightBookedEvent(BaseEvent):
    """
    Event raised when a flight is successfully booked.
    
    This event captures all relevant information about the booking
    at the time it was created. It serves as the source of truth
    for reconstructing the booking state.
    """
    event_type: str = Field(default="FlightBooked", const=True)
    
    # Additional typed fields for better validation
    user_id: Optional[int] = None
    offer_id: str
    departure: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    price: float
    adults: int = 1
    
    def __init__(self, **data):
        """
        Initialize FlightBookedEvent.
        
        Automatically populates the data field with all booking information.
        """
        super().__init__(**data)
        # Ensure data dict contains all booking info
        if not self.data:
            self.data = {
                "user_id": self.user_id,
                "offer_id": self.offer_id,
                "departure": self.departure,
                "destination": self.destination,
                "depart_date": self.depart_date,
                "return_date": self.return_date,
                "price": self.price,
                "adults": self.adults
            }


class BookingCancelledEvent(BaseEvent):
    """
    Event raised when a booking is cancelled.
    
    Future implementation - prepared for when cancellation feature is added.
    """
    event_type: str = Field(default="BookingCancelled", const=True)
    
    booking_id: str
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "booking_id": self.booking_id,
                "cancellation_reason": self.cancellation_reason,
                "refund_amount": self.refund_amount
            }
