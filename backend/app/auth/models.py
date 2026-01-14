from sqlalchemy import Column, Integer, String, DateTime, Float, func
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Booking(Base):
    """
    Read Model for bookings.
    This table stores the projected state of bookings for efficient querying.
    The source of truth remains the Event Store.
    """
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, index=True)  # UUID
    user_id = Column(Integer, nullable=True, index=True)
    offer_id = Column(String(100), nullable=False, index=True)
    departure = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    depart_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    return_date = Column(String(10), nullable=True)
    price = Column(Float, nullable=False)
    adults = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="confirmed")
    created_at = Column(DateTime, server_default=func.now())
    event_id = Column(String(36), nullable=False, index=True)  # Reference to Event Store

