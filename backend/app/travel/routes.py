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
from app.cqrs import FlightQueries, BookingCommands
from app.cqrs.commands.booking_commands import BookFlightCommand, BookHotelCommand, BookPackageCommand


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
            budget=budget
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

@router.post("/book", response_model=BookingOut)
async def book_flight(
    command: BookFlightCommand,
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
        result = await commands.book_flight(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


@router.post("/book/hotel", response_model=BookingOut)
async def book_hotel(
    command: BookHotelCommand,
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Book a hotel (COMMAND - Write operation).
    """
    try:
        result = await commands.book_hotel(command)
        # Adapt result for generic BookingOut which expects flight fields
        # Ideally BookingOut should be generic too, but for speed we construct it or make it permissive
        # The frontend will need to handle this.
        # Let's assume BookingOut is loose or we return a dict that matches Pydantic constraints
        # Actually BookingOut in this file is Flight specific.
        # I need to update BookingOut or define HotelBookingOut. 
        # But for 'response_model=BookingOut', it expects specific fields.
        # I will update BookingOut in a separate chunk to be generic as well.
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotel booking failed: {str(e)}")


@router.post("/book/package", response_model=BookingOut)
async def book_package(
    command: BookPackageCommand,
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Book a package (COMMAND - Write operation).
    """
    try:
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


@router.get("/my-bookings", response_model=List[UserBookingOut])
async def get_my_bookings(
    user_id: int = Query(..., description="User ID to fetch bookings for"),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Get all bookings for the current user (QUERY - Read operation from Read Model).
    
    Query Parameters:
    - user_id: User ID (from JWT token in real implementation)
    
    Returns:
    - List of user's bookings ordered by creation date (newest first)
    """
    try:
        bookings = await queries.get_user_bookings(user_id)
        return bookings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookings: {str(e)}")



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


@router.get("/packages")
async def search_packages(
    departure: str = Query(..., min_length=2, description="Departure city/airport"),
    destination: str = Query(..., min_length=2, description="Destination city/airport"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD)")
):
    """
    Search for combined flight + hotel packages.
    """
    try:
        # Note: In a full CQRS refactor, this should be moved to a Query Handler
        service = TravelService()
        return await service.search_packages(departure, destination, depart_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Package search failed: {str(e)}")


<<<<<<< HEAD
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


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2, description="Search keyword (e.g. 'Lon', 'Par')")
):
    """
    Autocomplete for airports and cities.
    Returns: [{label, iata, name, country, type}, ...]
    """
    try:
        async with TravelProvider() as provider:
            return await provider.search_locations(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {str(e)}")


from app.auth.dependencies import get_current_user
from app.auth.models import User

@router.get("/my-bookings")
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Get all bookings for the current logged-in user.
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

=======
>>>>>>> cb27edd0d154d91d1fb62895c194ab5a83aea805
