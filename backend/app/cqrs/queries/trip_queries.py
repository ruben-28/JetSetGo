from typing import List, Dict, Optional
from app.auth.db import SessionLocal
from app.auth.models import Trip, Booking

class TripQueries:
    """
    Read Side Queries for Trips.
    """
    
    def get_user_trips(self, user_id: int) -> List[Dict]:
        """
        Get all trips for a user.
        """
        session = SessionLocal()
        try:
            trips = session.query(Trip).filter(Trip.user_id == user_id).all()
            return [self._map_trip(t) for t in trips]
        finally:
            session.close()

    def get_trip_details(self, trip_id: str, user_id: int) -> Optional[Dict]:
        """
        Get full details of a trip including all bookings.
        """
        session = SessionLocal()
        try:
            trip = session.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
            if not trip:
                return None
            
            bookings = session.query(Booking).filter(Booking.trip_id == trip_id).all()
            
            trip_data = self._map_trip(trip)
            trip_data["bookings"] = [self._map_booking(b) for b in bookings]
            
            return trip_data
        finally:
            session.close()

    def _map_trip(self, trip: Trip) -> Dict:
        return {
            "id": trip.id,
            "name": trip.name,
            "status": trip.status,
            "total_price": trip.total_price,
            "currency": trip.currency,
            "created_at": trip.created_at
        }

    def _map_booking(self, booking: Booking) -> Dict:
        return {
            "id": booking.id,
            "type": booking.booking_type,
            "status": booking.status,
            "price": booking.price,
            # Add dynamic fields based on type
            "details": {
                "departure": booking.departure,
                "destination": booking.destination,
                "hotel_name": booking.hotel_name,
                "activity_name": booking.activity_name,
                "date": booking.depart_date or booking.check_in or booking.activity_date
            }
        }
