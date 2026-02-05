"""
Simple test using existing seeded user
"""
import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Login with seeded user
        login = await client.post(
            "http://localhost:8001/auth/login",
            json={"username_or_email": "test@example.com", "password": "password"}
        )
        
        if login.status_code != 200:
            print(f"Login failed: {login.text}")
            return
        
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Book hotel
        booking = await client.post(
            "http://localhost:8001/travel/book/hotel",
            json={
                "hotel_name": "Grand Hotel",
                "hotel_city": "PAR",
                "check_in": "2026-03-01",
                "check_out": "2026-03-05",
                "price": 450.00,
                "adults": 2
            },
            headers=headers
        )
        
        print(f"Status: {booking.status_code}")
        print(f"Response: {booking.text}")
        
        if booking.status_code == 200:
            print("\n✅ SUCCESS!")
            print(json.dumps(booking.json(), indent=2))
        else:
            print(f"\n❌ FAILED")
            try:
                print(json.dumps(booking.json(), indent=2))
            except:
                pass

asyncio.run(test())
