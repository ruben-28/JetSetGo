"""
Authentication Database Configuration
Uses centralized SQL Server configuration from app.db.config
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.db.config import DATABASE_URL

# SQL Server engine configuration
# No connect_args needed (that was SQLite-specific)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency for database sessions.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
