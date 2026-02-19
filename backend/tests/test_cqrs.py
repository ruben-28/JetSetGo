import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
CQRS Implementation Test Script
Tests the refactored CQRS architecture with Event Sourcing.

This script tests:
1. Flight search using FlightQueries (Query side)
2. Booking creation using BookingCommands (Command side)
3. Event persistence in Event Store
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add backend app to path

from app.gateway import TravelGateway
from app.cqrs import FlightQueries, BookingCommands
from app.cqrs.commands.booking_commands import BookFlightCommand
from app.db.event_store import get_event_store


async def test_flight_queries():
    """Test CQRS Query side - Flight search (READ operation)"""
    print("=" * 60)
    print("TEST 1: Flight Queries (CQRS Query Side)")
    print("=" * 60)
    
    async with TravelGateway() as gateway:
        queries = FlightQueries(gateway)
        
        # Calculate dates
        tomorrow = datetime.now() + timedelta(days=1)
        next_week = datetime.now() + timedelta(days=8)
        
        depart_date = tomorrow.strftime("%Y-%m-%d")
        return_date = next_week.strftime("%Y-%m-%d")
        
        print(f"\n🔍 Searching flights from Paris to London")
        print(f"   Departure: {depart_date}")
        print(f"   Return: {return_date}")
        print(f"   Budget: 500")
        
        try:
            offers = await queries.search_flights(
                origin="Paris",
                destination="London",
                depart_date=depart_date,
                return_date=return_date,
                adults=1,
                budget=500
            )
            
            print(f"\n✅ Query successful!")
            print(f"   Found {len(offers)} offers within budget")
            
            if offers:
                print("\n   First 3 offers:")
                for i, offer in enumerate(offers[:3], 1):
                    print(f"   {i}. {offer['airline']} - ${offer['price']} - {offer['stops']} stops")
            
            return offers[0] if offers else None
            
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            return None


async def test_booking_commands(offer_data=None):
    """Test CQRS Command side - Booking creation (WRITE operation with Event Sourcing)"""
    print("\n" + "=" * 60)
    print("TEST 2: Booking Commands (CQRS Command Side + Event Sourcing)")
    print("=" * 60)
    
    commands = BookingCommands()
    
    # Create booking command
    tomorrow = datetime.now() + timedelta(days=1)
    next_week = datetime.now() + timedelta(days=8)
    
    if offer_data:
        command = BookFlightCommand(
            offer_id=offer_data['id'],
            departure=offer_data['departure'],
            destination=offer_data['destination'],
            depart_date=offer_data['depart_date'],
            return_date=offer_data.get('return_date'),
            price=offer_data['price'],
            adults=offer_data['adults'],
            user_id=1,
            user_email="test@example.com",
            user_name="Test User"
        )
    else:
        command = BookFlightCommand(
            offer_id="TEST-BOOKING-001",
            departure="Paris",
            destination="London",
            depart_date=tomorrow.strftime("%Y-%m-%d"),
            return_date=next_week.strftime("%Y-%m-%d"),
            price=299.99,
            adults=2,
            user_id=1,
            user_email="test@example.com",
            user_name="Test User"
        )
    
    print(f"\n📝 Creating booking:")
    print(f"   From: {command.departure} to {command.destination}")
    print(f"   Dates: {command.depart_date} - {command.return_date}")
    print(f"   Price: ${command.price}")
    print(f"   Adults: {command.adults}")
    
    try:
        result = await commands.book_flight(command)
        
        print(f"\n✅ Booking successful!")
        print(f"   Booking ID: {result['booking_id']}")
        print(f"   Event ID: {result['event_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Created: {result['created_at']}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Booking failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_event_store(booking_result=None):
    """Test Event Store - Verify events are persisted"""
    print("\n" + "=" * 60)
    print("TEST 3: Event Store Verification")
    print("=" * 60)
    
    event_store = get_event_store()
    
    try:
        # Count total events
        total_events = await event_store.count_events()
        print(f"\n📊 Total events in store: {total_events}")
        
        # Get FlightBooked events
        all_events = await event_store.get_all(event_type="FlightBooked")
        print(f"   FlightBooked events: {len(all_events)}")
        
        if all_events:
            print("\n   Recent FlightBooked events:")
            for i, event in enumerate(all_events[-3:], 1):
                print(f"   {i}. Event ID: {event.event_id[:8]}...")
                print(f"      Aggregate ID: {event.aggregate_id[:8]}...")
                print(f"      Timestamp: {event.timestamp}")
                print(f"      Data: {event.data.get('departure')} → {event.data.get('destination')}")
                print()
        
        # If we have a booking result, verify its event
        if booking_result:
            print(f"\n🔍 Verifying event for booking {booking_result['booking_id'][:8]}...")
            events = await event_store.get_by_aggregate(booking_result['booking_id'])
            
            if events:
                print(f"✅ Found {len(events)} event(s) for this booking")
                event = events[0]
                print(f"   Event Type: {event.event_type}")
                print(f"   Event Data: {event.data}")
            else:
                print(f"❌ No events found for this booking!")
        
        print("\n✅ Event Store verification complete!")
        
    except Exception as e:
        print(f"\n❌ Event Store verification failed: {e}")
        import traceback
        traceback.print_exc()


async def test_cqrs_separation():
    """Test CQRS separation - Ensure queries don't modify state"""
    print("\n" + "=" * 60)
    print("TEST 4: CQRS Separation Verification")
    print("=" * 60)
    
    event_store = get_event_store()
    
    # Count events before query
    events_before = await event_store.count_events()
    print(f"\n📊 Events before query: {events_before}")
    
    # Execute a query
    async with TravelGateway() as gateway:
        queries = FlightQueries(gateway)
        
        tomorrow = datetime.now() + timedelta(days=1)
        next_week = datetime.now() + timedelta(days=8)
        
        await queries.search_flights(
            origin="Paris",
            destination="Berlin",
            depart_date=tomorrow.strftime("%Y-%m-%d"),
            return_date=next_week.strftime("%Y-%m-%d"),
            adults=1
        )
    
    # Count events after query
    events_after = await event_store.count_events()
    print(f"📊 Events after query: {events_after}")
    
    if events_before == events_after:
        print("\n✅ CQRS separation verified!")
        print("   Queries do NOT generate events (read-only)")
    else:
        print("\n❌ CQRS violation detected!")
        print("   Query operation generated events (should be read-only)")


async def main():
    """Run all CQRS tests"""
    print("\n" + "=" * 60)
    print("CQRS IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    print("\nTesting refactored backend with:")
    print("  • FlightQueries (Query side - reads)")
    print("  • BookingCommands (Command side - writes)")
    print("  • Event Sourcing (events stored BEFORE state changes)")
    print()
    
    # Test 1: Query side
    first_offer = await test_flight_queries()
    
    # Test 2: Command side
    booking_result = await test_booking_commands(first_offer)
    
    # Test 3: Event Store
    await test_event_store(booking_result)
    
    # Test 4: CQRS Separation
    await test_cqrs_separation()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
    print("\n✨ CQRS refactoring verification complete!")
    print("\nNext steps:")
    print("  1. Review event store database: jetsetgo_events.db")
    print("  2. Test via FastAPI endpoints: /travel/search, /travel/book")
    print("  3. Check Swagger docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
