"""
Query Module
Exports query handlers for read operations (CQRS pattern).
"""

from .flight_queries import FlightQueries

__all__ = ["FlightQueries"]
