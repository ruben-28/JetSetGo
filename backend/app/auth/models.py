import enum
from sqlalchemy import Column, Integer, String, DateTime, Float, func, Enum
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


class Booking(Base):
    """
    Read Model for bookings.
    This table stores the projected state of bookings for efficient querying.
    The source of truth remains the Event Store.
    """
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(Integer, nullable=True, index=True)
    
    # Generic fields
    booking_type = Column(Enum(BookingType), nullable=False, default=BookingType.FLIGHT)
    price = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="confirmed")
    created_at = Column(DateTime, server_default=func.now())
    event_id = Column(String(36), nullable=False, index=True)  # Reference to Event Store
    
    # Flight specific (make nullable)
    offer_id = Column(String(100), nullable=True, index=True)
    departure = Column(String(100), nullable=True)
    destination = Column(String(100), nullable=True)
    depart_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    return_date = Column(String(10), nullable=True)
    adults = Column(Integer, nullable=True, default=1)
    
    # Hotel / Package specific
    hotel_name = Column(String(200), nullable=True)
    hotel_city = Column(String(100), nullable=True)
    check_in = Column(String(10), nullable=True)  # YYYY-MM-DD
    check_out = Column(String(10), nullable=True)  # YYYY-MM-DD

