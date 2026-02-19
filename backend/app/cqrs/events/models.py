"""
Fichier: backend/app/cqrs/events/models.py
Objectif: Modèles d'événements pour l'Event Sourcing.
Responsabilités:
- Définir tous les événements métier qui capturent les changements d'état.
- Assurer la traçabilité et l'historisation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional, Literal
import uuid


class BaseEvent(BaseModel):
    """
    Classe de base pour tous les événements métier.
    
    Tous les événements du système héritent de cette classe pour assurer
    une structure cohérente et la traçabilité.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aggregate_id: str  # ID de l'entité concernée (ex: booking_id)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(default=1)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TripCreatedEvent(BaseEvent):
    """
    Événement levé lors de la création d'un nouveau voyage (conteneur de réservations).
    """
    event_type: Literal["TripCreated"] = "TripCreated"
    
    trip_id: str
    user_id: Optional[int]
    name: str
    total_price: float
    currency: str
    status: str
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "trip_id": self.trip_id,
                "user_id": self.user_id,
                "name": self.name,
                "total_price": self.total_price,
                "currency": self.currency,
                "status": self.status
            }


class FlightBookedEvent(BaseEvent):
    """
    Événement levé lorsqu'un vol est réservé avec succès.
    """
    event_type: Literal["FlightBooked"] = "FlightBooked"
    
    trip_id: Optional[str] = None
    user_id: Optional[int] = None
    offer_id: str
    departure: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    price: float
    adults: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "trip_id": self.trip_id,
                "user_id": self.user_id,
                "offer_id": self.offer_id,
                "departure": self.departure,
                "destination": self.destination,
                "depart_date": self.depart_date,
                "return_date": self.return_date,
                "price": self.price,
                "adults": self.adults
            }


class HotelBookedEvent(BaseEvent):
    """
    Événement levé lorsqu'un hôtel est réservé.
    """
    event_type: Literal["HotelBooked"] = "HotelBooked"
    
    trip_id: Optional[str] = None
    user_id: Optional[int] = None
    hotel_name: str
    hotel_city: str
    check_in: str
    check_out: str
    price: float
    adults: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "trip_id": self.trip_id,
                "user_id": self.user_id,
                "hotel_name": self.hotel_name,
                "hotel_city": self.hotel_city,
                "check_in": self.check_in,
                "check_out": self.check_out,
                "price": self.price,
                "adults": self.adults
            }


class ActivityBookedEvent(BaseEvent):
    """
    Événement levé lorsqu'une activité est réservée.
    """
    event_type: Literal["ActivityBooked"] = "ActivityBooked"
    
    trip_id: Optional[str] = None
    user_id: Optional[int] = None
    activity_name: str
    activity_date: str
    price: float
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "trip_id": self.trip_id,
                "user_id": self.user_id,
                "activity_name": self.activity_name,
                "activity_date": self.activity_date,
                "price": self.price
            }


class PackageBookedEvent(BaseEvent):
    """
    Événement levé lorsqu'un package (Vol + Hôtel) est réservé.
    Événement combiné/Legacy. Idéalement décomposé en Trip + Bookings multiples.
    """
    event_type: Literal["PackageBooked"] = "PackageBooked"
    
    trip_id: Optional[str] = None
    user_id: Optional[int] = None
    offer_id: str
    departure: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    hotel_name: str
    hotel_city: str
    check_in: str
    check_out: str
    price: float
    adults: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "trip_id": self.trip_id,
                "user_id": self.user_id,
                "offer_id": self.offer_id,
                "departure": self.departure,
                "destination": self.destination,
                "depart_date": self.depart_date,
                "return_date": self.return_date,
                "hotel_name": self.hotel_name,
                "hotel_city": self.hotel_city,
                "check_in": self.check_in,
                "check_out": self.check_out,
                "price": self.price,
                "adults": self.adults
            }


class BookingCancelledEvent(BaseEvent):
    """
    Événement levé lorsqu'une réservation est annulée.
    
    Implémentation future - préparé pour quand la fonctionnalité d'annulation sera ajoutée.
    """
    event_type: Literal["BookingCancelled"] = "BookingCancelled"
    
    booking_id: str
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.data:
            self.data = {
                "booking_id": self.booking_id,
                "cancellation_reason": self.cancellation_reason,
                "refund_amount": self.refund_amount
            }
