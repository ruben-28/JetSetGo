"""
CQRS Module
Command Query Responsibility Segregation pattern implementation.

This module provides a clear separation between:
- Queries: Read operations (FlightQueries)
- Commands: Write operations (BookingCommands)
- Events: Domain events for Event Sourcing

Usage:
    from app.cqrs import FlightQueries, BookingCommands
"""

from .queries import FlightQueries
from .commands import BookingCommands
from .events import BaseEvent, FlightBookedEvent, BookingCancelledEvent

__all__ = [
    # Query handlers
    "FlightQueries",
    
    # Command handlers
    "BookingCommands",
    
    # Events
    "BaseEvent",
    "FlightBookedEvent",
    "BookingCancelledEvent"
]
