import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from httpx import AsyncClient
from app.main import app
from app.auth.models import User
from app.auth.security import create_access_token
from unittest.mock import patch, MagicMock, AsyncMock

# Mock Data
MOCK_FLIGHTS = [{
    "id": "FL-123",
    "departure": "PAR",
    "destination": "NYC",
    "depart_date": "2027-12-25",
    "return_date": "2027-12-30",
    "airline": "Air France",
    "price": 500.0,
    "duration_min": 480,
    "stops": 0,
    "score": 10.0,
    "mock": True
}]

MOCK_HOTELS = [{
    "id": "HT-123",
    "name": "Grand Hotel",
    "city": "NYC",
    "price": 1000.0,
    "currency": "EUR",
    "rating": 5
}]

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def auth_headers():
    # Create valid token for testing
    # sub must be stringified version of user ID (int) if get_current_user parses it as int
    access_token = create_access_token(payload={"sub": "1", "id": 1, "email": "test@example.com"})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.mark.asyncio
async def test_search_packages_flow(async_client):
    # Use AsyncMock or set return_value to a completed future
    with patch("app.gateway.travel_provider.TravelProvider.search_flights", new_callable=AsyncMock) as mock_flights, \
         patch("app.gateway.travel_provider.TravelProvider.search_hotels", new_callable=AsyncMock) as mock_hotels:
        
        mock_flights.return_value = MOCK_FLIGHTS
        mock_hotels.return_value = MOCK_HOTELS
        
        payload = {
            "origin": "PAR",
            "destination": "NYC",
            "depart_date": "2027-12-25",
            "return_date": "2027-12-30",
            "adults": 1
        }
        
        try:
            response = await async_client.post("/travel/packages/search", json=payload)
            assert response.status_code == 200
            data = response.json()
            
            if "error" in data:
                raise Exception(f"API Returned Error: {data['error']}")

            assert "flights" in data
            assert len(data["flights"]) > 0
            assert data["flights"][0]["id"] == "FL-123"
            assert "hotels" in data
            assert len(data["hotels"]) > 0
        except Exception:
            import traceback
            with open("trace_search.log", "w") as f:
                if 'response' in locals():
                    f.write(f"Response Status: {response.status_code}\n")
                    f.write(f"Response Body: {response.text}\n\n")
                else:
                    f.write("Response failure\n")
                traceback.print_exc(file=f)
            raise

@pytest.mark.asyncio
async def test_book_package_flow(async_client, auth_headers):
    # Mock Event Store append to avoid real DB persistence issues during simplistic tests
    # But for Integration we usually want DB. Let's rely on DB but mock Provider.
    
    with patch("app.db.event_store.EventStore.append") as mock_append:
        payload = {
            "offer_id": "FL-123",
            "departure": "PAR",
            "destination": "NYC",
            "depart_date": "2027-12-25",
            "return_date": "2027-12-30",
            "hotel_name": "Grand Hotel",
            "hotel_city": "NYC",
            "price": 1500.0,
            "adults": 1,
            "user_id": 1 # Matches token
        }
        
        # We need to mock the _create_booking_record SIDE EFFECT or let it run? 
        # If we let it run, it needs a DB session. 
        # The BookingCommands uses SessionLocal.
        # For this test, let's assume the DB is available (it is in dev).
        
    try:
        response = await async_client.post("/travel/book/package", json=payload, headers=auth_headers)
        
        # Expect 200 OK
        assert response.status_code == 200
        data = response.json()
        assert "booking_id" in data
        assert data["status"] == "CONFIRMED"
        
        # Verify Trips endpoint can see it (if DB write worked)
        # Note: If we mocked EventStore.append, the Command handler still calls _create_booking_record
        # So the Read Model should be updated.
        
        trip_id = data["booking_id"] # In our logic we returned trip_id as booking_id for packages
        
        response_trip = await async_client.get(f"/travel/trips/{trip_id}", headers=auth_headers)
        assert response_trip.status_code == 200
        trip_data = response_trip.json()
        assert trip_data["id"] == trip_id
        assert len(trip_data["bookings"]) >= 2 # Flight + Hotel
    except Exception:
        import traceback
        with open("trace_book.log", "w") as f:
            if 'response' in locals():
                f.write(f"Response Status: {response.status_code}\n")
                f.write(f"Response Body: {response.text}\n\n")
                try:
                    err_detail = response.json().get("detail", "No detail")
                    with open("error_detail.txt", "w") as ef:
                        ef.write(str(err_detail))
                except:
                    pass
            else:
                 f.write("Response variable unbound (Exception before response).\n")

            traceback.print_exc(file=f)
        raise
