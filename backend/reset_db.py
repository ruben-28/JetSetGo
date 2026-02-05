import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "jetsetgodb.database.windows.net")
DB_NAME = os.getenv("DB_NAME", "JetSetGoDB")
DB_USER = os.getenv("DB_USER", "jetsetgo_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "JetSetGo2024!")
DRIVER = "{ODBC Driver 18 for SQL Server}"

conn_str = f"DRIVER={DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};TrustServerCertificate=yes"

def reset_db():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("Dropping tables trips and bookings...")
    try:
        # FK dependency: bookings references trips? (If defined via SQL? Not explicitly in migrate_db)
        # But safest to drop bookings (child) first, then trips (parent).
        
        cursor.execute("IF OBJECT_ID('dbo.bookings', 'U') IS NOT NULL DROP TABLE bookings")
        cursor.execute("IF OBJECT_ID('dbo.trips', 'U') IS NOT NULL DROP TABLE trips")
        
        conn.commit()
        print("Success.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_db()
