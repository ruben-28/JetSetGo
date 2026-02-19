"""
Module de Requêtes Vols (Flight Queries)
Gestionnaire de requêtes pour les opérations de recherche de vols (Lecture seule, côté Query CQRS).

Ce module gère toutes les opérations de LECTURE pour les vols. Il ne modifie
AUCUN état dans le système - il se contente de récupérer et retourner des données.
"""

from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException

from app.gateway import TravelProvider


class FlightQueries:
    """
    Gestionnaire de requêtes pour les opérations liées aux vols.
    
    Côté Query CQRS - Responsabilités :
    - Rechercher des vols (lecture seule).
    - Obtenir les détails d'une offre (lecture seule).
    - Valider les paramètres de requête.
    - Appliquer les règles métier de lecture (filtrage, tri).
    - AUCUNE MODIFICATION D'ÉTAT.
    
    Cette classe se concentre uniquement sur la récupération de données et l'optimisation des requêtes.
    """
    
    def __init__(self, gateway: TravelProvider):
        """
        Initialise le gestionnaire avec la dépendance gateway.
        
        Args:
            gateway: Instance de TravelProvider pour les appels API externes.
        """
        self.gateway = gateway
    
    # ========================================================================
    # Méthodes de Requête Publiques
    # ========================================================================
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        budget: Optional[int] = None,
        max_stops: Optional[int] = None
    ) -> List[Dict]:
        """
        Rechercher des offres de vol (Opération de LECTURE).
        
        Flux de la requête :
        1. Valider les paramètres.
        2. Récupérer les données via le gateway.
        3. Appliquer les filtres (budget).
        4. Trier les résultats.
        5. Retourner les données.
        
        Args:
            origin: Ville/Aéroport de départ.
            destination: Ville/Aéroport d'arrivée.
            depart_date: Date de départ (YYYY-MM-DD).
            return_date: Date de retour (YYYY-MM-DD), optionnel.
            adults: Nombre de passagers adultes.
            budget: Budget maximum (filtre optionnel).
            max_stops: Nombre maximum d'escales (0=direct, 1=max 1 escale, None=tous).
        
        Returns:
            Liste d'offres de vol (filtrées et triées).
        
        Raises:
            HTTPException: En cas d'erreur de validation.
        """
        # 1. Valider les entrées
        self._validate_dates(depart_date, return_date)
        self._validate_adults(adults)
        self._validate_budget(budget)
        
        # 2. Récupérer les données depuis le gateway avec filtre max_stops
        offers = await self.gateway.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            max_stops=max_stops
        )
        
        # 3. Appliquer les règles métier (filtres de lecture)
        if budget:
            offers = self._filter_by_budget(offers, budget)
        
        # 4. Trier par prix
        offers = self._sort_by_price(offers)
        
        return offers
    
    async def get_offer_details(self, offer_id: str) -> Dict:
        """
        Obtenir les détails d'une offre spécifique (Opération de LECTURE).
        
        Args:
            offer_id: Identifiant unique de l'offre.
        
        Returns:
            Détails de l'offre.
        
        Raises:
            HTTPException: En cas d'erreur de validation.
        """
        # 1. Valider l'offer_id
        if not offer_id or not offer_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Invalid offer_id: must be a non-empty string"
            )
        
        # 2. Récupérer les détails depuis le gateway
        details = await self.gateway.get_offer_details(offer_id)
        
        return details
    
    # ========================================================================
    # Logique de Validation (Côté Query)
    # ========================================================================
    
    def _validate_dates(self, depart_date: str, return_date: Optional[str]):
        """
        Valider les dates de départ et de retour.
        
        Règles :
        - Les dates doivent être au format YYYY-MM-DD.
        - La date de départ doit être dans le futur.
        - La date de retour doit être après la date de départ (si fournie).
        """
        try:
            depart = datetime.strptime(depart_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Format de date de départ invalide. Utilisez YYYY-MM-DD."
            )
        
        # Vérifier si le départ est dans le futur
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if depart < today:
            raise HTTPException(
                status_code=400,
                detail="La date de départ doit être dans le futur."
            )
        
        # Valider la date de retour si fournie
        if return_date:
            try:
                return_dt = datetime.strptime(return_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Format de date de retour invalide. Utilisez YYYY-MM-DD."
                )
            
            if return_dt <= depart:
                raise HTTPException(
                    status_code=400,
                    detail="La date de retour doit être postérieure à la date de départ."
                )
    
    def _validate_adults(self, adults: int):
        """Valider le nombre d'adultes."""
        if adults < 1 or adults > 9:
            raise HTTPException(
                status_code=400,
                detail="Le nombre d'adultes doit être compris entre 1 et 9."
            )
    
    def _validate_budget(self, budget: Optional[int]):
        """Valider le budget si fourni."""
        if budget is not None and budget < 0:
            raise HTTPException(
                status_code=400,
                detail="Le budget doit être un nombre positif."
            )
    
    # ========================================================================
    # Règles Métier de Lecture
    # ========================================================================
    
    def _filter_by_budget(self, offers: List[Dict], budget: int) -> List[Dict]:
        """Filtrer les offres par budget maximum."""
        return [offer for offer in offers if offer["price"] <= budget]
    
    def _sort_by_price(self, offers: List[Dict]) -> List[Dict]:
        """Trier les offres par prix (croissant)."""
        return sorted(offers, key=lambda x: x["price"])
    
    # ========================================================================
    # Requête Réservations Utilisateur (Read Model)
    # ========================================================================
    
    async def get_user_bookings(self, user_id: int) -> List[Dict]:
        """
        Obtenir toutes les réservations pour un utilisateur spécifique (LECTURE depuis le Read Model).
        
        Args:
            user_id: ID de l'utilisateur.
        
        Returns:
            Liste des enregistrements de réservation pour l'utilisateur.
        """
        from app.auth.db import SessionLocal
        from app.auth.models import Booking, BookingType
        
        session = SessionLocal()
        try:
            bookings = (
                session.query(Booking)
                .filter(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
                .all()
            )
            
            results = []
            for b in bookings:
                booking_dict = {
                    "id": b.id,
                    "booking_type": b.booking_type.value if hasattr(b.booking_type, 'value') else b.booking_type,
                    "price": b.price,
                    "adults": b.adults,
                    "status": b.status.value if hasattr(b.status, 'value') else b.status,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                    "event_id": b.event_id
                }
                
                # Champs polymorphiques
                if b.booking_type == BookingType.FLIGHT or b.booking_type == "FLIGHT":
                    booking_dict.update({
                        "offer_id": b.offer_id,
                        "departure": b.departure,
                        "destination": b.destination,
                        "depart_date": b.depart_date,
                        "return_date": b.return_date,
                    })
                elif b.booking_type == BookingType.HOTEL or b.booking_type == "HOTEL":
                    booking_dict.update({
                        "hotel_name": b.hotel_name,
                        "hotel_city": b.hotel_city,
                        "check_in": b.check_in,
                        "check_out": b.check_out,
                    })
                elif b.booking_type == BookingType.PACKAGE or b.booking_type == "PACKAGE":
                    booking_dict.update({
                        "offer_id": b.offer_id,
                        "departure": b.departure,
                        "destination": b.destination,
                        "depart_date": b.depart_date,
                        "return_date": b.return_date,
                        "hotel_name": b.hotel_name,
                        "hotel_city": b.hotel_city,
                        "check_in": b.check_in,
                        "check_out": b.check_out,
                    })
                
                results.append(booking_dict)
                
            return results
        finally:
            session.close()

