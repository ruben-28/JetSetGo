"""
Module CQRS (Command Query Responsibility Segregation)
Implémentation du pattern de ségrégation des responsabilités Commande/Requête.

Ce module fournit une séparation claire entre :
- Requêtes (Queries) : Opérations de lecture (FlightQueries).
- Commandes (Commands) : Opérations d'écriture (BookingCommands).
- Événements (Events) : Événements métier pour l'Event Sourcing.

Usage:
    from app.cqrs import FlightQueries, BookingCommands
"""

from .queries import FlightQueries
from .commands import BookingCommands
from .events import BaseEvent, FlightBookedEvent, BookingCancelledEvent

__all__ = [
    # Gestionnaires de Requêtes
    "FlightQueries",
    
    # Gestionnaires de Commandes
    "BookingCommands",
    
    # Événements
    "BaseEvent",
    "FlightBookedEvent",
    "BookingCancelledEvent"
]
