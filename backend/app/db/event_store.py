"""
Implémentation Event Store
Gère la persistance et la récupération des événements du domaine pour l'Event Sourcing.
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
# Configuration Base de Données
# ============================================================================

Base = declarative_base()


class EventModel(Base):
    """
    Modèle SQLAlchemy pour le stockage des événements.
    
    Stocke tous les événements domaine en mode append-only pour l'event sourcing.
    Chaque événement représente un changement d'état dans le système.
    """
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, index=True)
    aggregate_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    data = Column(NVARCHAR(None), nullable=False)  # Données événement sérialisées JSON (NVARCHAR(MAX) Unicode)
    version = Column(Integer, nullable=False, default=1)


# ============================================================================
# Classe Event Store
# ============================================================================

class EventStore:
    """
    Event Store pour persister et récupérer les événements domaine.
    
    Responsabilités:
    - Ajouter de nouveaux événements au store (append-only)
    - Récupérer les événements par ID d'agrégat
    - Récupérer tous les événements (pour scénarios de reconstruction/rejeu)
    - Assurer l'immutabilité des événements une fois stockés
    """
    
    def __init__(self):
        """
        Initialise l'Event Store avec une connexion SQL Server.
        
        Utilise DATABASE_URL centralisé depuis app.db.config.
        L'auth et l'event store partagent la même base de données cloud.
        """
        from app.db.config import DATABASE_URL
        
        self.engine = create_engine(
            DATABASE_URL,
            echo=False,  # Mettre à True pour le débogage
            pool_pre_ping=True,  # Vérifier les connexions avant utilisation
            pool_recycle=3600,  # Recycler les connexions après 1 heure
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Créer les tables si elles n'existent pas
        Base.metadata.create_all(bind=self.engine)
    
    async def append(self, event: BaseEvent) -> None:
        """
        Ajouter un nouvel événement à l'event store.
        
        Les événements sont immuables et append-only. Une fois stockés, ils ne peuvent être modifiés.
        
        Args:
            event: Événement domaine à stocker
            
        Raises:
            ValueError: Si un événement avec le même event_id existe déjà
        """
        session = self.SessionLocal()
        try:
            # Vérifier si l'événement existe déjà (idempotence)
            existing = session.query(EventModel).filter_by(event_id=event.event_id).first()
            if existing:
                raise ValueError(f"L'événement avec ID {event.event_id} existe déjà")
            
            # Créer le modèle d'événement
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
        Récupérer tous les événements pour un agrégat spécifique.
        
        Les événements sont retournés par ordre chronologique (par timestamp).
        Cela permet de reconstruire l'état courant d'un agrégat depuis ses événements.
        
        Args:
            aggregate_id: ID de l'agrégat (ex: booking_id)
            
        Returns:
            Liste des événements pour l'agrégat, ordonnés par timestamp
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
        Récupérer tous les événements du store.
        
        Utile pour:
        - Reconstruire les modèles de lecture
        - Scénarios de rejeu d'événements
        - Audit et débogage
        
        Args:
            event_type: Filtre optionnel par type d'événement
            
        Returns:
            Liste de tous les événements, ordonnés par timestamp
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
        Compter les événements dans le store.
        
        Args:
            aggregate_id: Filtre optionnel par ID d'agrégat
            
        Returns:
            Nombre d'événements
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
# Instance Globale Event Store
# ============================================================================

# Instance singleton pour utilisation à l'échelle de l'application
_event_store_instance: Optional[EventStore] = None


def get_event_store() -> EventStore:
    """
    Obtenir ou créer l'instance globale de l'event store.
    
    Returns:
        Instance EventStore
    """
    global _event_store_instance
    
    if _event_store_instance is None:
        _event_store_instance = EventStore()
    
    return _event_store_instance
