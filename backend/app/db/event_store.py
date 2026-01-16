"""
Event Store Implementation
Handles persistence and retrieval of domain events for Event Sourcing.
"""

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional
import json
import os

from app.cqrs.events.models import BaseEvent


# ============================================================================
# Database Setup
# ============================================================================

Base = declarative_base()


class EventModel(Base):
    """
    SQLAlchemy model for event storage.
    
    Stores all domain events in append-only fashion for event sourcing.
    Each event represents a state change in the system.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    aggregate_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    data = Column(NVARCHAR(None), nullable=False)  # JSON serialized event data (NVARCHAR(MAX) Unicode)
    version = Column(Integer, nullable=False, default=1)


# ============================================================================
# Event Store Class
# ============================================================================

class EventStore:
    """
    Event Store for persisting and retrieving domain events.
    
    Responsibilities:
    - Append new events to the store (append-only)
    - Retrieve events by aggregate ID
    - Retrieve all events (for rebuild/replay scenarios)
    - Ensure events are immutable once stored
    """
    
    def __init__(self):
        """
        Initialize Event Store with SQL Server connection.
        
        Uses centralized DATABASE_URL from app.db.config.
        Both auth and event store share the same cloud database.
        """
        from app.db.config import DATABASE_URL
        
        self.engine = create_engine(
            DATABASE_URL,
            echo=False,  # Set to True for debugging
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    async def append(self, event: BaseEvent) -> None:
        """
        Append a new event to the event store.
        
        Events are immutable and append-only. Once stored, they cannot be modified.
        
        Args:
            event: Domain event to store
            
        Raises:
            ValueError: If event with same event_id already exists
        """
        session = self.SessionLocal()
        try:
            # Check if event already exists (idempotency)
            existing = session.query(EventModel).filter_by(event_id=event.event_id).first()
            if existing:
                raise ValueError(f"Event with ID {event.event_id} already exists")
            
            # Create event model
            event_model = EventModel(
                event_id=event.event_id,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                data=json.dumps(event.data),
                version=event.version
            )
            
            session.add(event_model)
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    async def get_by_aggregate(self, aggregate_id: str) -> List[BaseEvent]:
        """
        Retrieve all events for a specific aggregate.
        
        Events are returned in chronological order (by timestamp).
        This allows rebuilding the current state of an aggregate from its events.
        
        Args:
            aggregate_id: ID of the aggregate (e.g., booking_id)
            
        Returns:
            List of events for the aggregate, ordered by timestamp
        """
        session = self.SessionLocal()
        try:
            event_models = (
                session.query(EventModel)
                .filter_by(aggregate_id=aggregate_id)
                .order_by(EventModel.timestamp)
                .all()
            )
            
            events = []
            for model in event_models:
                event = BaseEvent(
                    event_id=model.event_id,
                    aggregate_id=model.aggregate_id,
                    event_type=model.event_type,
                    timestamp=model.timestamp,
                    data=json.loads(model.data),
                    version=model.version
                )
                events.append(event)
            
            return events
            
        finally:
            session.close()
    
    async def get_all(self, event_type: Optional[str] = None) -> List[BaseEvent]:
        """
        Retrieve all events from the store.
        
        Useful for:
        - Rebuilding read models
        - Event replay scenarios
        - Audit and debugging
        
        Args:
            event_type: Optional filter by event type
            
        Returns:
            List of all events, ordered by timestamp
        """
        session = self.SessionLocal()
        try:
            query = session.query(EventModel).order_by(EventModel.timestamp)
            
            if event_type:
                query = query.filter_by(event_type=event_type)
            
            event_models = query.all()
            
            events = []
            for model in event_models:
                event = BaseEvent(
                    event_id=model.event_id,
                    aggregate_id=model.aggregate_id,
                    event_type=model.event_type,
                    timestamp=model.timestamp,
                    data=json.loads(model.data),
                    version=model.version
                )
                events.append(event)
            
            return events
            
        finally:
            session.close()
    
    async def count_events(self, aggregate_id: Optional[str] = None) -> int:
        """
        Count events in the store.
        
        Args:
            aggregate_id: Optional filter by aggregate ID
            
        Returns:
            Number of events
        """
        session = self.SessionLocal()
        try:
            query = session.query(EventModel)
            
            if aggregate_id:
                query = query.filter_by(aggregate_id=aggregate_id)
            
            return query.count()
            
        finally:
            session.close()


# ============================================================================
# Global Event Store Instance
# ============================================================================

# Singleton instance for application-wide use
_event_store_instance: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """
    Get or create the global event store instance.
    
    Returns:
        EventStore instance
    """
    global _event_store_instance
    
    if _event_store_instance is None:
        _event_store_instance = EventStore()
    
    return _event_store_instance
