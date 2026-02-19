import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
SQL Server Connection Test Script
Tests database connectivity and table creation for JetSetGo backend.
"""

from sqlalchemy import text
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_database_connection():
    """Test basic database connectivity."""
    print("=" * 70)
    print("TEST 1: Database Connection")
    print("=" * 70)
    
    try:
        from app.db.config import DATABASE_URL
        from sqlalchemy import create_engine
        
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS test")).scalar()
            assert result == 1
            print("✓ Database connection successful")
            print(f"✓ Connected to: {engine.url.database}")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_auth_tables():
    """Test auth database tables creation."""
    print("\n" + "=" * 70)
    print("TEST 2: Auth Tables Creation")
    print("=" * 70)
    
    try:
        from app.auth.db import Base, engine
        from app.auth.models import User, Booking
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ Auth tables created successfully")
        
        # Verify tables exist
        with engine.connect() as conn:
            # Check users table
            result = conn.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_NAME = 'users'"
            )).scalar()
            assert result == 1
            print("✓ Table 'users' exists")
            
            # Check bookings table
            result = conn.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_NAME = 'bookings'"
            )).scalar()
            assert result == 1
            print("✓ Table 'bookings' exists")
            
        return True
    except Exception as e:
        print(f"✗ Auth tables test failed: {e}")
        return False


def test_event_store():
    """Test event store initialization."""
    print("\n" + "=" * 70)
    print("TEST 3: Event Store Initialization")
    print("=" * 70)
    
    try:
        from app.db.event_store import get_event_store
        
        # Initialize event store
        event_store = get_event_store()
        print("✓ Event store initialized")
        
        # Verify events table exists
        with event_store.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_NAME = 'events'"
            )).scalar()
            assert result == 1
            print("✓ Table 'events' exists")
            
        return True
    except Exception as e:
        print(f"✗ Event store test failed: {e}")
        return False


def test_table_schemas():
    """Test table schemas match expected structure."""
    print("\n" + "=" * 70)
    print("TEST 4: Table Schemas Verification")
    print("=" * 70)
    
    try:
        from app.auth.db import engine
        
        with engine.connect() as conn:
            # Check users table columns
            users_cols = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'users' ORDER BY ORDINAL_POSITION"
            )).fetchall()
            users_col_names = [col[0] for col in users_cols]
            expected_users = ['id', 'username', 'email', 'password_hash', 'created_at']
            assert all(col in users_col_names for col in expected_users)
            print(f"✓ Users table schema correct: {users_col_names}")
            
            # Check events table columns
            events_cols = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'events' ORDER BY ORDINAL_POSITION"
            )).fetchall()
            events_col_names = [col[0] for col in events_cols]
            expected_events = ['id', 'event_id', 'aggregate_id', 'event_type', 'timestamp', 'data', 'version']
            assert all(col in events_col_names for col in expected_events)
            print(f"✓ Events table schema correct: {events_col_names}")
            
            # Check bookings table columns
            bookings_cols = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_NAME = 'bookings' ORDER BY ORDINAL_POSITION"
            )).fetchall()
            bookings_col_names = [col[0] for col in bookings_cols]
            expected_bookings = ['id', 'user_id', 'offer_id', 'departure', 'destination']
            assert all(col in bookings_col_names for col in expected_bookings)
            print(f"✓ Bookings table schema correct: {bookings_col_names}")
            
        return True
    except Exception as e:
        print(f"✗ Schema verification failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SQL SERVER MIGRATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Check environment variables
    print("\nEnvironment Variables:")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = value if var != 'DB_PASSWORD' else '***' + value[-3:] if len(value) > 3 else '***'
            print(f"  {var}: {display_value}")
        else:
            print(f"  {var}: ❌ NOT SET")
    
    print()
    
    # Run tests
    results = []
    results.append(("Connection", test_database_connection()))
    results.append(("Auth Tables", test_auth_tables()))
    results.append(("Event Store", test_event_store()))
    results.append(("Table Schemas", test_table_schemas()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<50} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! SQL Server migration successful!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
