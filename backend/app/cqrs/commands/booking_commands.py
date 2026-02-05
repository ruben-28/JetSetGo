"""
Booking Commands Module
Command handler for booking operations (write operations, CQRS Command side).

This module handles all WRITE operations for bookings. Each command:
1. Validates the request
2. Generates a domain event
3. Persists the event FIRST (Event Sourcing)
4. Applies state changes to the database
"""

from typing import Dict, Optional
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
import uuid

from app.db.event_store import get_event_store
from app.cqrs.events.models import (
    FlightBookedEvent, 
    HotelBookedEvent, 
    PackageBookedEvent, 
    BookingCancelledEvent, 
    TripCreatedEvent, 
    ActivityBookedEvent
)


# ============================================================================
# Command Models (Input DTOs)
# ============================================================================

class BookFlightCommand(BaseModel):
    """
    Command to book a flight.
    
    This represents the user's intent to create a booking.
    """
    offer_id: str = Field(..., min_length=1, description="Unique offer identifier")
    departure: str = Field(..., min_length=2, description="Departure city/airport")
    destination: str = Field(..., min_length=2, description="Destination city/airport")
    depart_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Return date (YYYY-MM-DD)")
    price: float = Field(..., gt=0, description="Booking price")
    adults: int = Field(default=1, ge=1, le=9, description="Number of adults")
    
    # Optional user information (if authenticated)
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Payment information (placeholder for future implementation)
    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('depart_date', 'return_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class CancelBookingCommand(BaseModel):
    """
    Command to cancel a booking.
    
    Future implementation - prepared for cancellation feature.
    """
    booking_id: str = Field(..., description="Booking ID to cancel")
    user_id: Optional[int] = None

    cancellation_reason: Optional[str] = None


class BookHotelCommand(BaseModel):
    """
    Command to book a hotel.
    """
    hotel_name: str = Field(..., min_length=2, description="Name of the hotel")
    hotel_city: str = Field(..., min_length=2, description="City of the hotel")
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    price: float = Field(..., gt=0, description="Booking price")
    adults: int = Field(default=1, ge=1, le=9, description="Number of adults")
    
    # Optional user information
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('check_in', 'check_out')
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class BookPackageCommand(BaseModel):
    """
    Command to book a package (Flight + Hotel).
    """
    offer_id: str = Field(..., min_length=1, description="Unique offer identifier for flight")
    departure: str = Field(..., min_length=2, description="Departure city/airport")
    destination: str = Field(..., min_length=2, description="Destination city/airport")
    depart_date: str = Field(..., description="Departure/Check-in date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Return/Check-out date (YYYY-MM-DD)")
    
    hotel_name: str = Field(..., min_length=2, description="Name of the hotel")
    hotel_city: str = Field(..., min_length=2, description="City of the hotel")
    
    price: float = Field(..., gt=0, description="Booking price")
    adults: int = Field(default=1, ge=1, le=9, description="Number of adults")
    
    # Optional user information
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Activity fields (Optional)
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None
    activity_date: Optional[str] = None
    activity_price: Optional[float] = None

    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('depart_date', 'return_date')
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


# ============================================================================
# Command Handler
# ============================================================================

class BookingCommands:
    """
    Command handler for booking-related write operations.
    
    CQRS Command Side - Responsibilities:
    - Process booking commands (write operations)
    - Validate command data
    - Generate domain events
    - Persist events FIRST (Event Sourcing pattern)
    - Apply state changes to database
    - Return command results
    
    Event Sourcing Pattern:
    Each command follows the flow:
    1. Validate command
    2. Generate event
    3. Save event to event store
    4. Apply state change
    5. Return result
    
    This ensures events are the source of truth, and state changes
    can always be reconstructed from events.
    """
    
    def __init__(self):
        """Initialize command handler with event store."""
        self.event_store = get_event_store()
    
    # ========================================================================
    # Public Command Methods
    # ========================================================================
    
    async def book_flight(self, command: BookFlightCommand) -> Dict:
        """
        Book a flight (WRITE operation with Event Sourcing).
        
        Command Flow (Event Sourcing):
        1. Validate the booking command
        2. Generate FlightBookedEvent
        3. Save event to event store FIRST
        4. Apply state change (create booking record)
        5. Return booking confirmation
        
        Args:
            command: BookFlightCommand with all booking details
        
        Returns:
            Booking confirmation with booking_id and event_id
        
        Raises:
            HTTPException: On validation errors or booking failures
        """
        # 1. Validate command
        self._validate_booking_command(command)
        
        # 2. Generate IDs
        trip_id = str(uuid.uuid4())
        booking_id = str(uuid.uuid4())
        
        # 3. Create Events
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Flight to {command.destination}",
            total_price=command.price,
            currency="EUR",
            status="CONFIRMED"
        )
        
        event = FlightBookedEvent(
            aggregate_id=booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            offer_id=command.offer_id,
            departure=command.departure,
            destination=command.destination,
            depart_date=command.depart_date,
            return_date=command.return_date,
            price=command.price,
            adults=command.adults,
            data={
                "booking_id": booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "user_email": command.user_email,
                "user_name": command.user_name,
                "offer_id": command.offer_id,
                "departure": command.departure,
                "destination": command.destination,
                "depart_date": command.depart_date,
                "return_date": command.return_date,
                "price": command.price,
                "adults": command.adults,
                "payment_method": command.payment_method,
                "status": "CONFIRMED",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 4. Save Event FIRST
        try:
            await self.event_store.append(trip_event)
            await self.event_store.append(event)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save booking event: {str(e)}"
            )
        
        # 5. Apply state change
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(booking_id, event)
        
        return {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "event_id": event.event_id,
            "status": "CONFIRMED",
            "offer_id": command.offer_id,
            "departure": command.departure,
            "destination": command.destination,
            "depart_date": command.depart_date,
            "return_date": command.return_date,
            "price": command.price,
            "adults": command.adults,
            "created_at": event.timestamp.isoformat(),
            "message": "Flight booked successfully (Trip created)"
        }
    
    async def cancel_booking(self, command: CancelBookingCommand) -> Dict:
        """
        Cancel a booking (WRITE operation with Event Sourcing).
        
        Future implementation - prepared for cancellation feature.
        
        Args:
            command: CancelBookingCommand with cancellation details
        
        Returns:
            Cancellation confirmation
        """
        # 1. Validate command
        if not command.booking_id:
            raise HTTPException(
                status_code=400,
                detail="Booking ID is required"
            )
        
        # 2. Create cancellation event
        event = BookingCancelledEvent(
            aggregate_id=command.booking_id,
            booking_id=command.booking_id,
            cancellation_reason=command.cancellation_reason,
            refund_amount=None  # To be implemented
        )
        
        # 3. Save event
        await self.event_store.append(event)
        
        # 4. Apply state change (update booking status)
        # To be implemented
        
        return {
            "booking_id": command.booking_id,
            "event_id": event.event_id,
            "status": "cancelled",
            "message": "Booking cancelled successfully"
        }

    async def book_hotel(self, command: BookHotelCommand) -> Dict:
        """
        Book a hotel (WRITE operation with Event Sourcing).
        """
        # 1. Validate
        self._validate_hotel_command(command)
        
        # 2. Generate IDs
        trip_id = str(uuid.uuid4())
        booking_id = str(uuid.uuid4())
        
        # 3. Create Events
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Hotel stay at {command.hotel_name}",
            total_price=command.price,
            currency="EUR",
            status="CONFIRMED"
        )
        
        event = HotelBookedEvent(
            aggregate_id=booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            hotel_name=command.hotel_name,
            hotel_city=command.hotel_city,
            check_in=command.check_in,
            check_out=command.check_out,
            price=command.price,
            adults=command.adults,
            data={
                "booking_id": booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "user_email": command.user_email,
                "user_name": command.user_name,
                "hotel_name": command.hotel_name,
                "hotel_city": command.hotel_city,
                "check_in": command.check_in,
                "check_out": command.check_out,
                "price": command.price,
                "adults": command.adults,
                "payment_method": command.payment_method,
                "status": "CONFIRMED",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 4. Save Event FIRST
        try:
            await self.event_store.append(trip_event)
            await self.event_store.append(event)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        # 5. Apply State Change
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(booking_id, event)
        
        return {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "event_id": event.event_id,
            "status": "CONFIRMED",
            "hotel_name": command.hotel_name,
            "check_in": command.check_in,
            "price": command.price,
            "created_at": event.timestamp.isoformat(),
            "message": "Hotel booked successfully (Trip created)"
        }

    async def book_package(self, command: BookPackageCommand) -> Dict:
        """
        Book a package (WRITE operation with Event Sourcing).
        """
        # 1. Validate
        self._validate_package_command(command)
        
        # 2. Generate IDs
        trip_id = str(uuid.uuid4())
        flight_booking_id = str(uuid.uuid4())
        hotel_booking_id = str(uuid.uuid4())
        activity_booking_id = str(uuid.uuid4()) if command.activity_id else None
        
        events_to_append = []
        
        # 3. Create Trip Event
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Trip to {command.destination}",
            total_price=command.price, # Assumes price is total
            currency="EUR",
            status="CONFIRMED"
        )
        events_to_append.append(trip_event)
        
        # 4. Create Flight Event
        flight_event = FlightBookedEvent(
            aggregate_id=flight_booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            offer_id=command.offer_id,
            departure=command.departure,
            destination=command.destination,
            depart_date=command.depart_date,
            return_date=command.return_date,
            price=0.0, # Price split logic simplified for now
            adults=command.adults,
            data={
                "booking_id": flight_booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "offer_id": command.offer_id,
                "departure": command.departure,
                "destination": command.destination,
                "depart_date": command.depart_date,
                "return_date": command.return_date,
                "price": 0.0,
                "adults": command.adults
            }
        )
        events_to_append.append(flight_event)
        
        # 5. Create Hotel Event
        hotel_event = HotelBookedEvent(
            aggregate_id=hotel_booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            hotel_name=command.hotel_name,
            hotel_city=command.hotel_city,
            check_in=command.depart_date,
            check_out=command.return_date if command.return_date else command.depart_date,
            price=0.0,
            adults=command.adults,
            data={
                "booking_id": hotel_booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "hotel_name": command.hotel_name,
                "hotel_city": command.hotel_city,
                "check_in": command.depart_date,
                "check_out": command.return_date,
                "price": 0.0,
                "adults": command.adults
            }
        )
        events_to_append.append(hotel_event)
        
        # 6. Create Activity Event (Optional)
        activity_event = None
        if command.activity_id:
            activity_event = ActivityBookedEvent(
                aggregate_id=activity_booking_id,
                trip_id=trip_id,
                user_id=command.user_id,
                activity_name=command.activity_name or "Activity",
                activity_date=command.activity_date or command.depart_date,
                price=command.activity_price or 0.0,
                data={
                    "booking_id": activity_booking_id,
                    "trip_id": trip_id,
                    "user_id": command.user_id,
                    "activity_name": command.activity_name,
                    "activity_date": command.activity_date,
                    "price": command.activity_price
                }
            )
            events_to_append.append(activity_event)
        
        # 7. Save Events
        try:
            for evt in events_to_append:
                await self.event_store.append(evt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        # 8. Apply State Changes
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(flight_booking_id, flight_event)
        await self._create_booking_record(hotel_booking_id, hotel_event)
        if activity_event:
            await self._create_booking_record(activity_booking_id, activity_event)
            
        return {
            "booking_id": trip_id, # Recurring Trip ID as main ref
            "trip_id": trip_id,
            "event_id": trip_event.event_id,
            "price": command.price,
            "adults": command.adults,
            "created_at": trip_event.timestamp.isoformat(),
            "status": "CONFIRMED",
            "message": "Package booked successfully"
        }
    
    # ========================================================================
    # Validation Logic (Command Side)
    # ========================================================================
    
    def _validate_booking_command(self, command: BookFlightCommand):
        """
        Validate booking command.
        
        Business rules for booking:
        - Offer ID must be valid
        - Departure date must be in the future
        - Return date must be after departure (if provided)
        - Price must be positive
        """
        # Validate dates
        try:
            depart = datetime.strptime(command.depart_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid departure date format"
            )
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if depart < today:
            raise HTTPException(
                status_code=400,
                detail="Cannot book flights in the past"
            )
        
        if command.return_date:
            try:
                return_dt = datetime.strptime(command.return_date, "%Y-%m-%d")
                if return_dt <= depart:
                    raise HTTPException(
                        status_code=400,
                        detail="Return date must be after departure date"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid return date format"
                )
        
        # Validate price
        if command.price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Price must be positive"
            )

    def _validate_hotel_command(self, command: BookHotelCommand):
        try:
            check_in = datetime.strptime(command.check_in, "%Y-%m-%d")
            check_out = datetime.strptime(command.check_out, "%Y-%m-%d")
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid date")
             
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if check_in < today:
             raise HTTPException(status_code=400, detail="Check-in must be in future")
        
        if check_out <= check_in:
             raise HTTPException(status_code=400, detail="Check-out must be after check-in")
             
    def _validate_package_command(self, command: BookPackageCommand):
        # Similar reuse of logic
        try:
            dep = datetime.strptime(command.depart_date, "%Y-%m-%d")
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid date")
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if dep < today:
             raise HTTPException(status_code=400, detail="Departure in past")
    
    # ========================================================================
    # State Application (Write Model)
    # ========================================================================
    
    async def _create_trip_record(self, trip_id: str, event: TripCreatedEvent) -> Dict:
        """
        Create trip record in Read Model.
        """
        from app.auth.db import SessionLocal
        from app.auth.models import Trip
        
        session = SessionLocal()
        try:
            trip = Trip(
                id=trip_id,
                user_id=event.user_id,
                name=event.name,
                total_price=event.total_price,
                currency=event.currency,
                status=event.status
            )
            session.add(trip)
            session.commit()
            return {"id": trip_id}
        except Exception as e:
            session.rollback()
            print(f"Failed to create trip record: {e}")
            raise e # Propagate error to reveal cause
        finally:
            session.close()

    async def _create_booking_record(
        self, 
        booking_id: str, 
        event: BaseModel 
    ) -> Dict:
        from app.auth.db import SessionLocal
        from app.auth.models import Booking, BookingType, BookingStatus
        
        session = SessionLocal()
        try:
            # Extract price from event - check both direct attribute and data dict
            event_price = getattr(event, "price", None)
            if event_price is None and hasattr(event, "data") and isinstance(event.data, dict):
                event_price = event.data.get("price", 0.0)
            if event_price is None:
                event_price = 0.0
            
            # Extract adults similarly
            event_adults = getattr(event, "adults", None)
            if event_adults is None and hasattr(event, "data") and isinstance(event.data, dict):
                event_adults = event.data.get("adults", 1)
            if event_adults is None:
                event_adults = 1
            
            booking_data = {
                "id": booking_id,
                "trip_id": getattr(event, "trip_id", None),
                "user_id": event.user_id,
                "price": float(event_price),  # Ensure it's a float
                "adults": int(event_adults),  # Ensure it's an int
                "status": BookingStatus.CONFIRMED,
                "event_id": event.event_id,
            }

            if event.event_type == "FlightBooked":
                booking_data.update({
                    "booking_type": BookingType.FLIGHT,
                    "offer_id": event.offer_id,
                    "departure": event.departure,
                    "destination": event.destination,
                    "depart_date": event.depart_date,
                    "return_date": event.return_date,
                })
            elif event.event_type == "HotelBooked":
                booking_data.update({
                    "booking_type": BookingType.HOTEL,
                    "hotel_name": event.hotel_name,
                    "hotel_city": event.hotel_city,
                    "check_in": event.check_in,
                    "check_out": event.check_out,
                })
            elif event.event_type == "ActivityBooked":
                booking_data.update({
                    "booking_type": BookingType.ACTIVITY,
                    "activity_name": event.activity_name,
                    "activity_date": event.activity_date,
                })
            elif event.event_type == "PackageBooked":
                # Legacy support or direct package mapping
                 booking_data.update({
                    "booking_type": BookingType.PACKAGE,
                    "offer_id": event.offer_id,
                    "departure": event.departure,
                    "destination": event.destination,
                    "hotel_name": event.hotel_name
                })

            booking = Booking(**booking_data)
            session.add(booking)
            session.commit()
            session.refresh(booking)
            
            return {"id": booking.id}
            
        except Exception as e:
            session.rollback()
            # CRITICAL: Read Model is out of sync with Event Store
            logger_msg = f"CRITICAL: Failed to persist booking {booking_id} to read model: {e}"
            print(logger_msg)
            raise HTTPException(
                status_code=500, 
                detail=f"Booking confirmed but failed to update view. Reference: {booking_id}. Error: {e}"
            )
        finally:
            session.close()

