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
from app.cqrs.events.models import FlightBookedEvent, BookingCancelledEvent


# ============================================================================
# Command Models (Input DTOs)
# ============================================================================

class BookFlightCommand(BaseModel):
    """
    Command to book a flight.
    
    This represents the user's intent to create a booking.
    """
    offer_id: str = Field(..., min_length=5, description="Unique offer identifier")
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
        
        # 2. Generate unique booking ID (aggregate ID)
        booking_id = str(uuid.uuid4())
        
        # 3. Create domain event
        event = FlightBookedEvent(
            aggregate_id=booking_id,
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
                "status": "confirmed",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 4. CRITICAL: Save event FIRST (Event Sourcing)
        try:
            await self.event_store.append(event)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save booking event: {str(e)}"
            )
        
        # 5. Apply state change (create booking in read model)
        # Note: In a full Event Sourcing implementation, this would be handled
        # by a separate event handler/projection. For now, we do it directly.
        booking = await self._create_booking_record(booking_id, command, event)
        
        # 6. Return confirmation
        return {
            "booking_id": booking_id,
            "event_id": event.event_id,
            "status": "confirmed",
            "offer_id": command.offer_id,
            "departure": command.departure,
            "destination": command.destination,
            "depart_date": command.depart_date,
            "return_date": command.return_date,
            "price": command.price,
            "adults": command.adults,
            "created_at": event.timestamp.isoformat(),
            "message": "Flight booked successfully"
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
    
    # ========================================================================
    # State Application (Write Model)
    # ========================================================================
    
    async def _create_booking_record(
        self, 
        booking_id: str, 
        command: BookFlightCommand,
        event: FlightBookedEvent
    ) -> Dict:
        """
        Create booking record in database (apply state change).
        
        Note: In a full CQRS/ES architecture, this would be handled by
        a separate projection/event handler that listens to events.
        For now, we apply the state change directly after saving the event.
        
        Args:
            booking_id: Unique booking identifier
            command: Original booking command
            event: Persisted booking event
        
        Returns:
            Created booking record
        """
        # TODO: Implement actual database persistence
        # For now, we'll just return a confirmation
        # In a full implementation, this would insert into a bookings table
        
        booking_record = {
            "id": booking_id,
            "user_id": command.user_id,
            "offer_id": command.offer_id,
            "departure": command.departure,
            "destination": command.destination,
            "depart_date": command.depart_date,
            "return_date": command.return_date,
            "price": command.price,
            "adults": command.adults,
            "status": "confirmed",
            "created_at": event.timestamp,
            "event_id": event.event_id
        }
        
        # TODO: Save to database
        # db.add(Booking(**booking_record))
        # db.commit()
        
        return booking_record
