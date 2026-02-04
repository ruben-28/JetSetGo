"""
Complete Database Migration: Allow NULL for all flight-specific columns
Fixes hotel booking errors by making flight columns nullable.
"""

from app.auth.db import engine
from sqlalchemy import text

print("=" * 60)
print("COMPLETE DATABASE MIGRATION")
print("Making all flight-specific columns nullable")
print("=" * 60)

# All columns that need to be nullable for hotel bookings
migrations = [
    "ALTER TABLE bookings ALTER COLUMN offer_id VARCHAR(100) NULL;",
    "ALTER TABLE bookings ALTER COLUMN departure VARCHAR(100) NULL;",
    "ALTER TABLE bookings ALTER COLUMN destination VARCHAR(100) NULL;",
    "ALTER TABLE bookings ALTER COLUMN depart_date VARCHAR(10) NULL;",
    "ALTER TABLE bookings ALTER COLUMN return_date VARCHAR(10) NULL;",
]

print("\nExecuting migrations...")
success_count = 0
error_count = 0

try:
    with engine.connect() as conn:
        for i, sql in enumerate(migrations, 1):
            try:
                print(f"\n[{i}/{len(migrations)}] {sql.strip()}")
                conn.execute(text(sql))
                conn.commit()
                print("    SUCCESS")
                success_count += 1
            except Exception as e:
                print(f"    ERROR: {e}")
                error_count += 1
                
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print(f"MIGRATION COMPLETE: {success_count} successful, {error_count} errors")
print("=" * 60)

if success_count > 0:
    print("\nSUCCESS: Hotel bookings should now work!")
    print("You can test booking a hotel now.")
