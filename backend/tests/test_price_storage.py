import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test script to verify price is being stored correctly in bookings
"""
from app.auth.db import SessionLocal
from app.auth.models import Booking, BookingType, BookingStatus
import uuid

# Create a test booking with a known price
session = SessionLocal()
try:
    test_booking = Booking(
        id=str(uuid.uuid4()),
        user_id=1,
        booking_type=BookingType.FLIGHT,
        price=999.99,  # Test price
        adults=2,
        status=BookingStatus.CONFIRMED,
        event_id=str(uuid.uuid4()),
        departure="PAR",
        destination="NYC"
    )
    
    session.add(test_booking)
    session.commit()
    session.refresh(test_booking)
    
    print(f"Created test booking: ID={test_booking.id}, Price={test_booking.price}")
    
    # Now query it back
    queried = session.query(Booking).filter(Booking.id == test_booking.id).first()
    print(f"Queried back: ID={queried.id}, Price={queried.price}")
    
    if queried.price == 999.99:
        print("✅ SUCCESS: Price is being stored and retrieved correctly!")
    else:
        print(f"❌ FAIL: Expected 999.99, got {queried.price}")
        
finally:
    session.close()
