"""
Database Schema Verification Script
Checks and creates all required tables in SQL Server.
"""

from app.auth.db import Base, engine
from app.auth.models import User, Booking, BookingType
from app.db.event_store import EventStore

print("=" * 60)
print("DATABASE SCHEMA VERIFICATION")
print("=" * 60)

# Import all models to ensure they're registered
print("\n✅ Models imported successfully")
print(f"   - User")
print(f"   - Booking (types: {[t.value for t in BookingType]})")

# Create all tables
print("\n🔨 Creating/Updating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # List all tables
    print("\n📋 Registered tables:")
    for table in Base.metadata.sorted_tables:
        print(f"   - {table.name}")
        print(f"     Columns: {[c.name for c in table.columns]}")
    
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()

# Test connection
print("\n🔗 Testing database connection...")
try:
    from app.auth.db import SessionLocal
    session = SessionLocal()
    
    # Try a simple query
    result = session.execute("SELECT COUNT(*) FROM users")
    user_count = result.scalar()
    print(f"✅ Connection successful! Found {user_count} users.")
    
    # Check bookings table
    result = session.execute("SELECT COUNT(*) FROM bookings")
    booking_count = result.scalar()
    print(f"✅ Bookings table exists! Found {booking_count} bookings.")
    
    session.close()
except Exception as e:
    print(f"❌ Connection test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
