"""Simple test for price storage"""
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Login
        r = await client.post(
            "http://localhost:8001/auth/login",
            json={"username_or_email": "test@example.com", "password": "password"}
        )
        
        if r.status_code != 200:
            print(f"Login failed: {r.status_code}")
            return
        
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Book flight with price
        booking = await client.post(
            "http://localhost:8001/travel/book-flight",
            json={
                "offer_id": "TEST_PRICE",
                "departure": "PAR",
                "destination": "NYC",
                "depart_date": "2026-03-01",
                "return_date": "2026-03-10",
                "price": 599.99,
                "adults": 2
            },
            headers=headers
        )
        
        print(f"Booking status: {booking.status_code}")
        if booking.status_code == 200:
            result = booking.json()
            print(f"Booking ID: {result.get('booking_id')}")
            print(f"Price in response: {result.get('price')}")
            
            # Check database
            bookings = await client.get(
                "http://localhost:8001/travel/my-bookings",
                headers=headers
            )
            
            if bookings.status_code == 200:
                all_bookings = bookings.json()
                if all_bookings:
                    latest = all_bookings[0]
                    print(f"\nLatest booking price from DB: {latest.get('price')}")
                    if latest.get('price') == 599.99:
                        print("✅ SUCCESS! Price is stored correctly!")
                    else:
                        print(f"❌ FAIL: Price is {latest.get('price')}, expected 599.99")
        else:
            print(f"Booking failed: {booking.text}")

asyncio.run(main())
