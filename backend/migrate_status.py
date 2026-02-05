"""
Quick script to update existing booking statuses from lowercase to uppercase.
"""
from app.auth.db import SessionLocal
from app.auth.models import Booking
from sqlalchemy import text

def migrate_status():
    session = SessionLocal()
    try:
        # Update all lowercase 'confirmed' to uppercase 'CONFIRMED'
        result = session.execute(
            text("UPDATE bookings SET status = 'CONFIRMED' WHERE LOWER(status) = 'confirmed'")
        )
        session.commit()
        print(f"Updated {result.rowcount} booking records")
        
        # Also update trips if needed
        result2 = session.execute(
            text("UPDATE trips SET status = 'CONFIRMED' WHERE LOWER(status) = 'confirmed'")
        )
        session.commit()
        print(f"Updated {result2.rowcount} trip records")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_status()
