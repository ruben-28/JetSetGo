import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Quick test to verify the price fix works with the booking API
"""
import httpx
import asyncio

async def test_booking_with_price():
    async with httpx.AsyncClient() as client:
        # First, login
        login_response = await client.post(
            "http://localhost:8001/auth/login",
            json={"username_or_email": "test@example.com", "password": "password"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Book a flight with a specific price
        booking_payload = {
            "offer_id": "TEST_FLIGHT_123",
            "departure": "PAR",
            "destination": "NYC",
            "depart_date": "2026-03-01",
            "return_date": "2026-03-10",
            "price": 599.99,  # Specific test price
            "adults": 2
        }
        
        booking_response = await client.post(
            "http://localhost:8001/travel/book-flight",
            json=booking_payload,
            headers=headers
        )
        
        if booking_response.status_code != 200:
            print(f"❌ Booking failed: {booking_response.text}")
            return
        
        booking_result = booking_response.json()
        print(f"✅ Booking created: {booking_result['booking_id']}")
        print(f"   Price in response: {booking_result.get('price', 'NOT FOUND')}")
        
        # Now fetch bookings to see if price is stored
        bookings_response = await client.get(
            "http://localhost:8001/travel/my-bookings",
            headers=headers
        )
        
        if bookings_response.status_code != 200:
            print(f"❌ Failed to fetch bookings: {bookings_response.text}")
            return
        
        bookings = bookings_response.json()
        latest_booking = bookings[0] if bookings else None
        
        if latest_booking:
            stored_price = latest_booking.get('price', 0)
            print(f"\n📊 Latest booking from database:")
            print(f"   ID: {latest_booking['id']}")
            print(f"   Price: {stored_price}")
            print(f"   Adults: {latest_booking.get('adults', 0)}")
            
            if stored_price == 599.99:
                print("\n🎉 SUCCESS! Price is now being stored correctly!")
            else:
                print(f"\n❌ FAIL: Expected 599.99, got {stored_price}")
        else:
            print("❌ No bookings found")

if __name__ == "__main__":
    asyncio.run(test_booking_with_price())
