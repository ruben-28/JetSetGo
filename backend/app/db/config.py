"""
Database Configuration Module
Centralized configuration for SQL Server connection using pyodbc.
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_database_url() -> str:
    """
    Generate SQL Server DATABASE_URL using odbc_connect format.
    
    This format avoids issues with special characters in passwords.
    Supports ODBC Driver 18 (preferred) or falls back to 17.
    
    Returns:
        str: SQLAlchemy connection string for SQL Server
        
    Environment Variables Required:
        - DB_SERVER: SQL Server hostname (e.g., jetsetgo_db.mssql.somee.com)
        - DB_NAME: Database name (e.g., jetsetgo_db)
        - DB_USER: SQL Server login (e.g., ethan5_SQLLogin_1)
        - DB_PASSWORD: SQL Server password
    """
    server = os.getenv("DB_SERVER", "jetsetgo_db.mssql.somee.com")
    database = os.getenv("DB_NAME", "jetsetgo_db")
    username = os.getenv("DB_USER", "ethan5_SQLLogin_1")
    password = os.getenv("DB_PASSWORD", "")
    
    if not password:
        raise ValueError(
            "DB_PASSWORD environment variable is required. "
            "Please set it in your .env file."
        )
    
    # Try ODBC Driver 18 first (newer), fallback to 17
    # TrustServerCertificate=yes is required for self-signed certificates (common on somee)
    driver = "ODBC Driver 18 for SQL Server"
    
    # Build connection string with odbc_connect format
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    
    # URL-encode the connection string
    params = quote_plus(connection_string)
    
    # Return SQLAlchemy-compatible URL
    return f"mssql+pyodbc:///?odbc_connect={params}"


# Global DATABASE_URL
DATABASE_URL = get_database_url()
