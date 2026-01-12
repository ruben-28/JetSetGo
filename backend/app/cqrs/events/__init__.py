"""
Event Sourcing Module
Exports event models and base classes for the event sourcing infrastructure.
"""

from .models import BaseEvent, FlightBookedEvent, BookingCancelledEvent

__all__ = [
    "BaseEvent",
    "FlightBookedEvent", 
    "BookingCancelledEvent"
]
