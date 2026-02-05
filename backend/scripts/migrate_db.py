import os
import sys
import pyodbc
from dotenv import load_dotenv

# Add parent dir to path if needed (though we just need the sensitive env vars)
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Get connection string parts from env usually, but here we might need to construct it
# or use SQLAlchemy's URL. The error log showed: 
# [Microsoft][ODBC Driver 18 for SQL Server]
# So we need to connect similarly.

DB_SERVER = os.getenv("DB_SERVER", "jetsetgodb.database.windows.net")
DB_NAME = os.getenv("DB_NAME", "JetSetGoDB")
DB_USER = os.getenv("DB_USER", "jetsetgo_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "JetSetGo2024!")
DRIVER = "{ODBC Driver 18 for SQL Server}"

conn_str = f"DRIVER={DRIVER};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD};TrustServerCertificate=yes"

def migrate():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        print("Connected to database.")
        
        # Columns to add
        # booking_type (Enum/String), hotel_name, hotel_city, check_in, check_out
        
        alter_commands = [
            # Create Trips table
            """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='trips' AND xtype='U')
            CREATE TABLE trips (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(200) NULL,
                destination VARCHAR(100) NULL,
                start_date VARCHAR(10) NULL,
                end_date VARCHAR(10) NULL,
                total_price FLOAT DEFAULT 0.0,
                currency VARCHAR(3) DEFAULT 'EUR',
                status VARCHAR(20) DEFAULT 'CONFIRMED',
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE()
            );
            """,
            
            # Booking columns
            "ALTER TABLE bookings ADD trip_id VARCHAR(36) NULL;", 
            # Note: booking_type might exist from previous attempts, handling gracefully via try/catch loop is good, 
            # but 'IF NOT EXISTS' col check is better for SQL Server.
            # Using the try-catch block in the loop handles the 'Column already exists' error (42S21).
            
            "ALTER TABLE bookings ADD booking_type VARCHAR(20) NOT NULL DEFAULT 'FLIGHT';",
            "ALTER TABLE bookings ADD currency VARCHAR(3) DEFAULT 'EUR';",
            "ALTER TABLE bookings ADD provider_name VARCHAR(50) NULL;",
            "ALTER TABLE bookings ADD provider_id VARCHAR(100) NULL;",
            
            # Flight specific additions
            "ALTER TABLE bookings ADD airline VARCHAR(100) NULL;",
            "ALTER TABLE bookings ADD flight_number VARCHAR(20) NULL;",
            
            # Hotel/Package specific additions
            "ALTER TABLE bookings ADD hotel_name VARCHAR(200) NULL;",
            "ALTER TABLE bookings ADD hotel_city VARCHAR(100) NULL;",
            "ALTER TABLE bookings ADD check_in VARCHAR(10) NULL;",
            "ALTER TABLE bookings ADD check_out VARCHAR(10) NULL;",
            "ALTER TABLE bookings ADD room_type VARCHAR(100) NULL;",
            "ALTER TABLE bookings ADD guests INTEGER DEFAULT 1;",
            
            # Activity specific
            "ALTER TABLE bookings ADD activity_name VARCHAR(200) NULL;",
            "ALTER TABLE bookings ADD activity_date VARCHAR(10) NULL;",
            "ALTER TABLE bookings ADD activity_duration VARCHAR(50) NULL;"
        ]
        
        for cmd in alter_commands:
            try:
                print(f"Executing: {cmd}")
                cursor.execute(cmd)
                conn.commit()
                print("Success.")
            except pyodbc.ProgrammingError as e:
                # 42S21 means column already exists
                if "42S21" in str(e):
                    print("Column already exists, skipping.")
                else:
                    print(f"Error executing command: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

        print("Migration complete.")
        conn.close()
        
    except Exception as e:
        print(f"Connection failed: {e}")
        # Try to print env vars (masked) to debug connection
        print(f"Server: {DB_SERVER}")
        print(f"User: {DB_USER}")

if __name__ == "__main__":
    migrate()
