from sqlalchemy import inspect
from app.auth.db import engine
import sys

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    for table in ['trips', 'bookings']:
        if table in tables:
            print(f"\nColumns in {table}:")
            for col in inspector.get_columns(table):
                print(f"  - {col['name']} ({col['type']})")
        else:
            print(f"\nTable {table} NOT FOUND")

if __name__ == "__main__":
    try:
        check_tables()
    except Exception as e:
        print(f"Error: {e}")
