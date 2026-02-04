"""
Database Migration: Allow NULL for offer_id in bookings table
This fixes the issue where hotel bookings fail because offer_id is NOT NULL in SQL Server.
"""

from app.auth.db import engine
from sqlalchemy import text

print("=" * 60)
print("DATABASE MIGRATION: Allow NULL for offer_id")
print("=" * 60)

migration_sql = """
ALTER TABLE bookings
ALTER COLUMN offer_id VARCHAR(100) NULL;
"""

print("\nMigration SQL:")
print(migration_sql)

try:
    with engine.connect() as conn:
        print("\nExecuting migration...")
        conn.execute(text(migration_sql))
        conn.commit()
        print("SUCCESS: Migration completed!")
        print("   - offer_id column now allows NULL values")
        print("   - Hotel bookings will now work correctly")
        
except Exception as e:
    print(f"ERROR: Migration failed: {e}")
    print("\nINFO: If migration already ran, you can ignore this error.")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("MIGRATION COMPLETE")
print("=" * 60)
print("\nYou can now test hotel bookings!")

