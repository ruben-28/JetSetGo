import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(".").resolve()))

from desktop.app.services.async_api_client import AsyncApiClient

async def main():
    print("Initializing AsyncApiClient...")
    client = AsyncApiClient("http://localhost:8001")
    
    # Mock Token (Tests use valid tokens, here we simulate)
    # Ideally we should login first.
    print("Attempting Search...")
    
    def on_success(data):
        print("Search Success!")
        flights = data.get("flights", [])
        hotels = data.get("hotels", [])
        print(f"Found {len(flights)} flights and {len(hotels)} hotels")
        if len(flights) > 0:
            print(f"Sample Flight: {flights[0]['id']}")

    def on_error(err):
        print(f"Search Error: {err}")

    # We need to run the client which uses QThreadpool... 
    # Ah, AsyncApiClient depends on QObject and QThreadPool.
    # We can't easily run it without a QApplication instance if it uses QThreadPool.
    # Let's check `async_api_client.py` again.
    # It uses QThreadPool.
    
    # We need a minimal QApplication to test this.
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Cannot initialize QApplication: {e}")
        return

    # Call search
    client.get_packages_async(
        origin="PAR",
        destination="NYC",
        depart_date="2027-12-25",
        return_date="2027-12-30",
        adults=1,
        on_success=on_success,
        on_error=on_error
    )
    
    # Wait for search
    print("Waiting for search...")
    import time
    start = time.time()
    while time.time() - start < 3:
        app.processEvents()
        time.sleep(0.1)

    # Call Booking
    print("Attempting Booking...")
    def on_book_success(data):
        print(f"Booking Success! Trip ID: {data.get('booking_id')}")

    def on_book_error(err):
        print(f"Booking Error: {err}")

    booking_payload = {
        "offer_id": "FL-123",
        "departure": "PAR",
        "destination": "NYC",
        "depart_date": "2027-12-25",
        "return_date": "2027-12-30",
        "hotel_name": "Grand Hotel NYC",
        "hotel_city": "NYC",
        "price": 1250.00,
        "adults": 1
    }

    # Register a temp user to avoid DB state issues
    import time
    ts = int(time.time())
    username = f"user_{ts}"
    email = f"user_{ts}@example.com"
    password = "test123"  # Short password for bcrypt
    
    def on_login_success(data):
        print(f"Login Success. Token: {data['access_token'][:10]}...")
        client.set_token(data["access_token"])
        # Trigger booking now
        print("Triggering booking...")
        client.book_package_async(booking_payload, on_book_success, on_book_error)

    def on_register_success(data):
        print("Register Success, logging in...")
        client.login_async(email, password, on_login_success, on_error)

    print(f"Registering user {email}...")
    client.register_async(username, email, password, on_register_success, on_error)

    print("Waiting for login and booking...")
    start = time.time()
    while time.time() - start < 5:
        app.processEvents()
        time.sleep(0.1)
        
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
