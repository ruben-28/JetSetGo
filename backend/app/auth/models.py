import enum
from sqlalchemy import Column, Integer, String, DateTime, Float, func, Enum, ForeignKey
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class BookingType(str, enum.Enum):
    FLIGHT = "FLIGHT"
    HOTEL = "HOTEL"
    PACKAGE = "PACKAGE"
    ACTIVITY = "ACTIVITY"


class BookingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    HELD = "HELD"


class Trip(Base):
    """
    Trip model to group multiple bookings.
    """
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String(200), nullable=True, default="My Trip")
    
    # Snapshot of search parameters
    destination = Column(String(100), nullable=True)
    start_date = Column(String(10), nullable=True)
    end_date = Column(String(10), nullable=True)
    
    total_price = Column(Float, default=0.0)
    currency = Column(String(3), default="EUR")
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Booking(Base):
    """
    Read Model for bookings.
    This table stores the projected state of bookings for efficient querying.
    The source of truth remains the Event Store.
    """
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    trip_id = Column(String(36), index=True, nullable=True) # ForeignKey("trips.id")
    user_id = Column(Integer, nullable=True, index=True)
    
    # Generic fields
    booking_type = Column(Enum(BookingType), nullable=False, default=BookingType.FLIGHT)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.CONFIRMED)
    
    provider_name = Column(String(50), nullable=True)
    provider_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    event_id = Column(String(36), nullable=False, index=True)  # Reference to Event Store
    
    # Flight specific
    offer_id = Column(String(100), nullable=True, index=True)
    departure = Column(String(100), nullable=True)
    destination = Column(String(100), nullable=True)
    depart_date = Column(String(10), nullable=True)
    return_date = Column(String(10), nullable=True)
    airline = Column(String(100), nullable=True)
    flight_number = Column(String(20), nullable=True)
    adults = Column(Integer, nullable=True, default=1)
    
    # Hotel / Package specific
    hotel_name = Column(String(200), nullable=True)
    hotel_city = Column(String(100), nullable=True)
    check_in = Column(String(10), nullable=True)
    check_out = Column(String(10), nullable=True)
    room_type = Column(String(100), nullable=True)
    guests = Column(Integer, default=1)
    
    # Activity specific
    activity_name = Column(String(200), nullable=True)
    activity_date = Column(String(10), nullable=True)
    activity_duration = Column(String(50), nullable=True)

