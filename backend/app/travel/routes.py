"""
Travel Router Module
HTTP endpoints for travel-related operations using CQRS pattern.

CQRS Pattern Implementation:
- Query endpoints (GET) use FlightQueries for read operations
- Command endpoints (POST) use BookingCommands for write operations
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.gateway import TravelProvider
from app.services.travel_service import TravelService
from app.cqrs import FlightQueries, BookingCommands
from app.cqrs.commands.booking_commands import BookFlightCommand, BookHotelCommand, BookPackageCommand
from app.cqrs.commands.search_commands import SearchCommands, SearchPackageCommand
from app.cqrs.commands.search_commands import SearchCommands, SearchPackageCommand
from app.cqrs.queries.trip_queries import TripQueries
from app.auth.dependencies import get_current_user
from app.auth.models import User


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/travel", tags=["travel"])


# ============================================================================
# Dependency Injection (CQRS Pattern)
# ============================================================================

async def get_flight_queries():
    """
    Dependency factory for FlightQueries (CQRS Query side).
    
    Creates gateway and query handler instances with proper cleanup.
    Used for all READ operations.
    """
    async with TravelProvider() as gateway:
        yield FlightQueries(gateway)


async def get_booking_commands():
    """
    Dependency factory for BookingCommands (CQRS Command side).
    
    Creates command handler instance.
    Used for all WRITE operations.
    """
    yield BookingCommands()


async def get_search_commands():
    """Dependency factory for SearchCommands."""
    yield SearchCommands()


async def get_trip_queries():
    """Dependency factory for TripQueries."""
    yield TripQueries()


# ============================================================================
# Response Models
# ============================================================================

class OfferOut(BaseModel):
    """Flight offer response model"""
    id: str
    departure: str
    destination: str
    depart_date: str
    return_date: str
    airline: str
    price: int
    duration_min: int
    stops: int
    score: float
    adults: int = Field(default=1)
    mock: bool = Field(default=False)


class OfferDetailsOut(BaseModel):
    """Offer details response model"""
    id: str
    baggage: str
    refund_policy: str
    notes: str
    hotel_suggestion: dict
    mock: bool = Field(default=False)


class BookingOut(BaseModel):
    """Booking confirmation response model"""
    booking_id: str
    trip_id: Optional[str] = None  # Added for trip reference
    event_id: str
    status: str
    price: float
    adults: int
    created_at: str
    message: str
    
    # Optional fields for different types
    offer_id: Optional[str] = None
    departure: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None


class LocationOut(BaseModel):
    """Location search response model"""
    name: str
    code: str
    type: str  # CITY or AIRPORT
    detail: str


# ============================================================================
# Query Endpoints (Read Operations - CQRS Query Side)
# ============================================================================

@router.get("/search", response_model=List[OfferOut])
async def search(
    departure: str = Query(..., min_length=2, description="Departure city/airport"),
    destination: str = Query(..., min_length=2, description="Destination city/airport"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Return date (YYYY-MM-DD)"),
    budget: Optional[int] = Query(None, ge=0, description="Maximum budget"),
    max_stops: Optional[int] = Query(None, ge=0, le=5, description="Max stops (0=direct, 1=max 1 stop, None=all)"),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Search for flight offers (QUERY - Read operation).
    
    CQRS Pattern: This endpoint uses FlightQueries for read-only operations.
    No state is modified, only data retrieval and filtering.
    
    Query Parameters:
    - departure: Departure city/airport IATA code (use /locations to find it)
    - destination: Destination city/airport IATA code (use /locations to find it)
    - depart_date: Departure date (YYYY-MM-DD)
    - return_date: Return date (YYYY-MM-DD)
    - budget: Maximum budget (optional)
    - max_stops: Maximum number of stops (0 = direct only, 1 = max 1 stop, None = all flights)
    
    Returns:
    - List of flight offers sorted by price
    """
    try:
        offers = await queries.search_flights(
            origin=departure,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=1,  # Default to 1 adult for backward compatibility
            budget=budget,
            max_stops=max_stops
        )
        return offers
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/details/{offer_id}", response_model=OfferDetailsOut)
async def details(
    offer_id: str,
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Get detailed information about a specific offer (QUERY - Read operation).
    
    CQRS Pattern: This endpoint uses FlightQueries for read-only operations.
    
    Path Parameters:
    - offer_id: Unique offer identifier
    
    Returns:
    - Detailed offer information
    """
    try:
        details = await queries.get_offer_details(offer_id)
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get details: {str(e)}")


# ============================================================================
# Command Endpoints (Write Operations - CQRS Command Side)
# ============================================================================

@router.post("/book")  # Removed response_model for consistency
async def book_flight(
    command: BookFlightCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Book a flight (COMMAND - Write operation with Event Sourcing).
    
    CQRS Pattern: This endpoint uses BookingCommands for write operations.
    
    Event Sourcing Flow:
    1. Validates the booking command
    2. Generates FlightBookedEvent
    3. Persists event to event store FIRST
    4. Applies state change (creates booking)
    5. Returns confirmation
    
    Request Body:
    - BookFlightCommand with all booking details
    
    Returns:
    - Booking confirmation with booking_id and event_id
    """
    try:
        # Enforce user_id from token
        command.user_id = current_user.id
        result = await commands.book_flight(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


@router.post("/book/hotel")  # Removed response_model temporarily for debugging
async def book_hotel(
    command: BookHotelCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Book a hotel (COMMAND - Write operation).
    """
    try:
        command.user_id = current_user.id
        result = await commands.book_hotel(command)
        # Return raw dict without Pydantic validation
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotel booking failed: {str(e)}")


@router.post("/book/package")  # Removed response_model for consistency
async def book_package(
    command: BookPackageCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Book a package (COMMAND - Write operation).
    """
    try:
        command.user_id = current_user.id
        result = await commands.book_package(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package booking failed: {str(e)}")


# ============================================================================
# User Bookings Endpoint (Read Model Query)
# ============================================================================

class UserBookingOut(BaseModel):
    """User booking response model"""
    id: str
    booking_type: str
    price: float
    adults: int
    status: str
    created_at: Optional[str]
    event_id: str
    
    # Flight fields
    offer_id: Optional[str] = None
    departure: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    
    # Hotel/Package fields
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None

# ============================================================================
# City/Airport Search Endpoint (for Autocomplete)
# ============================================================================

@router.get("/cities/search")
async def search_cities(
    keyword: str = Query(..., min_length=2, description="Search keyword (min 2 chars)"),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Search for cities and airports (for autocomplete).
    
    Query Parameters:
    - keyword: Search keyword (e.g., "Par" for Paris)
    
    Returns:
    - List of matching cities/airports with IATA codes
    """
    try:
        # Use FlightQueries gateway to access the search
        async with TravelProvider() as gateway:
            results = await gateway.search_cities(keyword)
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"City search failed: {str(e)}")


# ============================================================================
# New Endpoints for Packages and Hotels
# ============================================================================

@router.get("/hotels")
async def search_hotels(
    city_code: str = Query(..., min_length=3, description="City IATA code or name")
):
    """
    Search for hotels in a specific city.
    """
    try:
        service = TravelService()
        return await service.search_hotels(city_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")


@router.post("/packages/search")
async def search_packages_post(
    command: SearchPackageCommand,
    commands: SearchCommands = Depends(get_search_commands)
):
    """
    Search for combined flight + hotel packages (command style).
    """
    try:
        return await commands.search_packages(command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package search failed: {str(e)}")


@router.get("/trips/me")
async def get_my_trips(
    current_user: User = Depends(get_current_user),
    queries: TripQueries = Depends(get_trip_queries)
):
    """
    Get all trips for the current user.
    """
    try:
        return queries.get_user_trips(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trips: {str(e)}")


@router.get("/trips/{trip_id}")
async def get_trip_details(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    queries: TripQueries = Depends(get_trip_queries)
):
    """
    Get detailed trip information including all bookings.
    """
    try:
        trip = queries.get_trip_details(trip_id, current_user.id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        return trip
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trip details: {str(e)}")


# Redundant endpoints removed (autocomplete and repetitive search_hotels)


# Removed imports (moved to top)

@router.get("/my-bookings", response_model=List[UserBookingOut])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Get all bookings for the current logged-in user.
    Uses JWT token authentication to identify the user.
    """
    try:
        return await queries.get_user_bookings(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookings: {str(e)}")



@router.get("/locations", response_model=List[LocationOut])
async def get_locations(
    keyword: str = Query(..., min_length=2, description="Search keyword (e.g. 'Lon', 'Par')")
):
    """
    Autocomplete for airports and cities.
    
    Use this endpoint to get official IATA codes for the search endpoint.
    """
    try:
        async with TravelProvider() as provider:
            return await provider.search_locations(keyword)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location search failed: {str(e)}")

