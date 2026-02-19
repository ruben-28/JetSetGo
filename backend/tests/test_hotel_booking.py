import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test hotel booking directly to see the actual error
"""
import httpx
import asyncio
import json

async def test_hotel_booking():
    async with httpx.AsyncClient() as client:
        # First register a new user
        import time
        timestamp = int(time.time())
        
        register_data = {
            "email": f"testhotel{timestamp}@example.com",
            "password": "test123",  # Short password to avoid bcrypt error
            "username": f"testhotel{timestamp}"
        }
        
        reg_response = await client.post(
            "http://localhost:8001/auth/register",
            json=register_data
        )
        
        print(f"Registration: {reg_response.status_code}")
        
        if reg_response.status_code != 200:
            print(f"Registration failed: {reg_response.text}")
            return
        
        # Login
        login_response = await client.post(
            "http://localhost:8001/auth/login",
            json={
                "username_or_email": register_data["email"],
                "password": register_data["password"]
            }
        )
        
        print(f"Login: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Book hotel
        hotel_booking = {
            "hotel_name": "Test Hotel",
            "hotel_city": "PAR",
            "check_in": "2026-03-01",
            "check_out": "2026-03-05",
            "price": 299.99,
            "adults": 2
        }
        
        print(f"\nBooking hotel with data: {json.dumps(hotel_booking, indent=2)}")
        
        booking_response = await client.post(
            "http://localhost:8001/travel/book/hotel",
            json=hotel_booking,
            headers=headers
        )
        
        print(f"\nBooking response status: {booking_response.status_code}")
        print(f"Response headers: {dict(booking_response.headers)}")
        print(f"Response body: {booking_response.text}")
        
        if booking_response.status_code == 200:
            print("\n✅ SUCCESS! Hotel booking worked!")
            print(json.dumps(booking_response.json(), indent=2))
        else:
            print(f"\n❌ FAILED with status {booking_response.status_code}")
            try:
                error_detail = booking_response.json()
                print(f"Error detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Raw error: {booking_response.text}")

if __name__ == "__main__":
    asyncio.run(test_hotel_booking())
