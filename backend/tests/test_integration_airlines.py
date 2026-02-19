import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(dotenv_path="backend/.env")

from app.gateway.travel_provider import TravelProvider

async def test_integration():
    print("🚀 Starting Integration Test: TravelProvider + AmadeusService")
    
    async with TravelProvider() as provider:
        print("\n1. Searching for flights PAR -> JFK for tomorrow...")
        
        # Calculate tomorrow's date
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        results = await provider.search_flights(
            origin="PAR",
            destination="JFK",
            depart_date=tomorrow,
            depart_date=tomorrow
        )
        
        if not results:
            print("❌ No flights found. Check API quota or parameters.")
            return

        print(f"✅ Found {len(results)} flights.\n")
        
        print("2. Verifying airline names (should be full names, not codes)...")
        for flight in results[:3]:
            print(f"   ✈️  Flight {flight['id']}: {flight['airline']} ({flight['price']} EUR)")
            
            # Simple heuristic check: Code is usually 2 chars, Name is longer
            if len(flight['airline']) <= 2:
                 print(f"      ⚠️  WARNING: Airline name looks like a code: {flight['airline']}")
            else:
                 print(f"      ✅ OK")

    print("\n✅ Integration Test Completed.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_integration())
