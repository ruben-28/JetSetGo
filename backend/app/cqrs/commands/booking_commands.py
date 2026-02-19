"""
Module de Commandes de Réservation (Booking Commands)
Gestionnaire de commandes pour les opérations de réservation (Opérations d'écriture, côté Command CQRS).

Ce module gère toutes les opérations d'ÉCRITURE pour les réservations. Chaque commande :
1. Valide la requête.
2. Génère un événement métier.
3. Persiste l'événement EN PREMIER (Event Sourcing).
4. Applique les changements d'état à la base de données (Read Model).
"""

from typing import Dict, Optional
from datetime import datetime
from fastapi import HTTPException
from pydantic import BaseModel, Field, validator
import uuid

from app.db.event_store import get_event_store
from app.cqrs.events.models import (
    FlightBookedEvent, 
    HotelBookedEvent, 
    PackageBookedEvent, 
    BookingCancelledEvent, 
    TripCreatedEvent, 
    ActivityBookedEvent
)


# ============================================================================
# Modèles de Commande (DTOs d'Entrée)
# ============================================================================

class BookFlightCommand(BaseModel):
    """
    Commande pour réserver un vol.
    
    Représente l'intention de l'utilisateur de créer une réservation.
    """
    offer_id: str = Field(..., min_length=1, description="Identifiant unique de l'offre")
    departure: str = Field(..., min_length=2, description="Ville/Aéroport de départ")
    destination: str = Field(..., min_length=2, description="Ville/Aéroport de destination")
    depart_date: str = Field(..., description="Date de départ (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Date de retour (YYYY-MM-DD)")
    price: float = Field(..., gt=0, description="Prix de la réservation")
    adults: int = Field(default=1, ge=1, le=9, description="Nombre d'adultes")
    
    # Informations utilisateur optionnelles (si authentifié)
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Informations de paiement (placeholder pour implémentation future)
    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('depart_date', 'return_date')
    def validate_date_format(cls, v):
        """Valider le format de date."""
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La date doit être au format YYYY-MM-DD")
        return v


class CancelBookingCommand(BaseModel):
    """
    Commande pour annuler une réservation.
    
    Implémentation future - préparé pour la fonctionnalité d'annulation.
    """
    booking_id: str = Field(..., description="ID de la réservation à annuler")
    user_id: Optional[int] = None

    cancellation_reason: Optional[str] = None


class BookHotelCommand(BaseModel):
    """
    Commande pour réserver un hôtel.
    """
    hotel_name: str = Field(..., min_length=2, description="Nom de l'hôtel")
    hotel_city: str = Field(..., min_length=2, description="Ville de l'hôtel")
    check_in: str = Field(..., description="Date d'arrivée (YYYY-MM-DD)")
    check_out: str = Field(..., description="Date de départ (YYYY-MM-DD)")
    price: float = Field(..., gt=0, description="Prix de la réservation")
    adults: int = Field(default=1, ge=1, le=9, description="Nombre d'adultes")
    
    # Informations utilisateur optionnelles
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('check_in', 'check_out')
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La date doit être au format YYYY-MM-DD")
        return v


class BookPackageCommand(BaseModel):
    """
    Commande pour réserver un package (Vol + Hôtel).
    """
    offer_id: str = Field(..., min_length=1, description="Identifiant unique de l'offre de vol")
    departure: str = Field(..., min_length=2, description="Ville/Aéroport de départ")
    destination: str = Field(..., min_length=2, description="Ville/Aéroport de destination")
    depart_date: str = Field(..., description="Date de départ/Check-in (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Date de retour/Check-out (YYYY-MM-DD)")
    
    hotel_name: str = Field(..., min_length=2, description="Nom de l'hôtel")
    hotel_city: str = Field(..., min_length=2, description="Ville de l'hôtel")
    
    price: float = Field(..., gt=0, description="Prix de la réservation")
    adults: int = Field(default=1, ge=1, le=9, description="Nombre d'adultes")
    
    # Informations utilisateur optionnelles
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    # Champs Activité (Optionnel)
    activity_id: Optional[str] = None
    activity_name: Optional[str] = None
    activity_date: Optional[str] = None
    activity_price: Optional[float] = None

    payment_method: Optional[str] = Field(default="credit_card")
    
    @validator('depart_date', 'return_date')
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("La date doit être au format YYYY-MM-DD")
        return v


# ============================================================================
# Gestionnaire de Commandes (Command Handler)
# ============================================================================

class BookingCommands:
    """
    Gestionnaire de commandes pour les opérations d'écriture liées aux réservations.
    
    Côté Command CQRS - Responsabilités :
    - Traiter les commandes de réservation (opérations d'écriture).
    - Valider les données de la commande.
    - Générer des événements de domaine.
    - Persister les événements EN PREMIER (Pattern Event Sourcing).
    - Appliquer les changements d'état à la base de données.
    - Retourner les résultats de la commande.
    
    Pattern Event Sourcing :
    Chaque commande suit le flux :
    1. Valider la commande
    2. Générer l'événement
    3. Sauvegarder l'événement dans l'Event Store
    4. Appliquer le changement d'état
    5. Retourner le résultat
    
    Cela garantit que les événements sont la source de vérité, et que l'état
    peut toujours être reconstruit à partir des événements.
    """
    
    def __init__(self):
        """Initialiser le gestionnaire avec l'Event Store."""
        self.event_store = get_event_store()
    
    # ========================================================================
    # Méthodes de Commande Publiques
    # ========================================================================
    
    async def book_flight(self, command: BookFlightCommand) -> Dict:
        """
        Réserver un vol (Opération d'ÉCRITURE avec Event Sourcing).
        
        Flux de la Commande (Event Sourcing) :
        1. Valider la commande de réservation.
        2. Générer FlightBookedEvent.
        3. Sauvegarder l'événement dans l'Event Store EN PREMIER.
        4. Appliquer le changement d'état (créer l'enregistrement de réservation).
        5. Retourner la confirmation de réservation.
        
        Args:
            command: BookFlightCommand avec tous les détails de la réservation.
        
        Returns:
            Confirmation de réservation avec booking_id et event_id.
        
        Raises:
            HTTPException: En cas d'erreur de validation ou d'échec de réservation.
        """
        # 1. Valider la commande
        self._validate_booking_command(command)
        
        # 2. Générer les IDs
        trip_id = str(uuid.uuid4())
        booking_id = str(uuid.uuid4())
        
        # 3. Créer les Événements
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Flight to {command.destination}",
            total_price=command.price,
            currency="EUR",
            status="CONFIRMED"
        )
        
        event = FlightBookedEvent(
            aggregate_id=booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            offer_id=command.offer_id,
            departure=command.departure,
            destination=command.destination,
            depart_date=command.depart_date,
            return_date=command.return_date,
            price=command.price,
            adults=command.adults,
            data={
                "booking_id": booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "user_email": command.user_email,
                "user_name": command.user_name,
                "offer_id": command.offer_id,
                "departure": command.departure,
                "destination": command.destination,
                "depart_date": command.depart_date,
                "return_date": command.return_date,
                "price": command.price,
                "adults": command.adults,
                "payment_method": command.payment_method,
                "status": "CONFIRMED",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 4. Sauvegarder l'Événement EN PREMIER
        try:
            await self.event_store.append(trip_event)
            await self.event_store.append(event)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Échec de sauvegarde de l'événement de réservation : {str(e)}"
            )
        
        # 5. Appliquer le changement d'état
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(booking_id, event)
        
        return {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "event_id": event.event_id,
            "status": "CONFIRMED",
            "offer_id": command.offer_id,
            "departure": command.departure,
            "destination": command.destination,
            "depart_date": command.depart_date,
            "return_date": command.return_date,
            "price": command.price,
            "adults": command.adults,
            "created_at": event.timestamp.isoformat(),
            "message": "Réservation de vol réussie (Voyage créé)"
        }
    
    async def cancel_booking(self, command: CancelBookingCommand) -> Dict:
        """
        Annuler une réservation (Opération d'ÉCRITURE avec Event Sourcing).
        
        Implémentation future - préparé pour la fonctionnalité d'annulation.
        
        Args:
            command: CancelBookingCommand avec les détails de l'annulation.
        
        Returns:
            Confirmation d'annulation.
        """
        # 1. Valider la commande
        if not command.booking_id:
            raise HTTPException(
                status_code=400,
                detail="Booking ID est requis"
            )
        
        # 2. Créer l'événement d'annulation
        event = BookingCancelledEvent(
            aggregate_id=command.booking_id,
            booking_id=command.booking_id,
            cancellation_reason=command.cancellation_reason,
            refund_amount=None  # À implémenter
        )
        
        # 3. Sauvegarder l'événement
        await self.event_store.append(event)
        
        # 4. Appliquer le changement d'état (mise à jour statut réservation)
        # À implémenter
        
        return {
            "booking_id": command.booking_id,
            "event_id": event.event_id,
            "status": "cancelled",
            "message": "Réservation annulée avec succès"
        }

    async def book_hotel(self, command: BookHotelCommand) -> Dict:
        """
        Réserver un hôtel (Opération d'ÉCRITURE avec Event Sourcing).
        """
        # 1. Valider
        self._validate_hotel_command(command)
        
        # 2. Générer les IDs
        trip_id = str(uuid.uuid4())
        booking_id = str(uuid.uuid4())
        
        # 3. Créer les Événements
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Séjour à l'hôtel {command.hotel_name}",
            total_price=command.price,
            currency="EUR",
            status="CONFIRMED"
        )
        
        event = HotelBookedEvent(
            aggregate_id=booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            hotel_name=command.hotel_name,
            hotel_city=command.hotel_city,
            check_in=command.check_in,
            check_out=command.check_out,
            price=command.price,
            adults=command.adults,
            data={
                "booking_id": booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "user_email": command.user_email,
                "user_name": command.user_name,
                "hotel_name": command.hotel_name,
                "hotel_city": command.hotel_city,
                "check_in": command.check_in,
                "check_out": command.check_out,
                "price": command.price,
                "adults": command.adults,
                "payment_method": command.payment_method,
                "status": "CONFIRMED",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 4. Sauvegarder l'Événement EN PREMIER
        try:
            await self.event_store.append(trip_event)
            await self.event_store.append(event)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        # 5. Appliquer le changement d'état
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(booking_id, event)
        
        return {
            "booking_id": booking_id,
            "trip_id": trip_id,
            "event_id": event.event_id,
            "status": "CONFIRMED",
            "hotel_name": command.hotel_name,
            "check_in": command.check_in,
            "price": command.price,
            "created_at": event.timestamp.isoformat(),
            "message": "Hôtel réservé avec succès (Voyage créé)"
        }

    async def book_package(self, command: BookPackageCommand) -> Dict:
        """
        Réserver un package (Opération d'ÉCRITURE avec Event Sourcing).
        """
        # 1. Valider
        self._validate_package_command(command)
        
        # 2. Générer les IDs
        trip_id = str(uuid.uuid4())
        flight_booking_id = str(uuid.uuid4())
        hotel_booking_id = str(uuid.uuid4())
        activity_booking_id = str(uuid.uuid4()) if command.activity_id else None
        
        events_to_append = []
        
        # 3. Créer l'Événement Voyage
        trip_event = TripCreatedEvent(
            aggregate_id=trip_id,
            trip_id=trip_id,
            user_id=command.user_id,
            name=f"Voyage à {command.destination}",
            total_price=command.price, # Suppose que le prix est total
            currency="EUR",
            status="CONFIRMED"
        )
        events_to_append.append(trip_event)
        
        # 4. Créer l'Événement Vol
        flight_event = FlightBookedEvent(
            aggregate_id=flight_booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            offer_id=command.offer_id,
            departure=command.departure,
            destination=command.destination,
            depart_date=command.depart_date,
            return_date=command.return_date,
            price=0.0, # Logique de séparation des prix simplifiée pour l'instant
            adults=command.adults,
            data={
                "booking_id": flight_booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "offer_id": command.offer_id,
                "departure": command.departure,
                "destination": command.destination,
                "depart_date": command.depart_date,
                "return_date": command.return_date,
                "price": 0.0,
                "adults": command.adults
            }
        )
        events_to_append.append(flight_event)
        
        # 5. Créer l'Événement Hôtel
        hotel_event = HotelBookedEvent(
            aggregate_id=hotel_booking_id,
            trip_id=trip_id,
            user_id=command.user_id,
            hotel_name=command.hotel_name,
            hotel_city=command.hotel_city,
            check_in=command.depart_date,
            check_out=command.return_date if command.return_date else command.depart_date,
            price=0.0,
            adults=command.adults,
            data={
                "booking_id": hotel_booking_id,
                "trip_id": trip_id,
                "user_id": command.user_id,
                "hotel_name": command.hotel_name,
                "hotel_city": command.hotel_city,
                "check_in": command.depart_date,
                "check_out": command.return_date,
                "price": 0.0,
                "adults": command.adults
            }
        )
        events_to_append.append(hotel_event)
        
        # 6. Créer l'Événement Activité (Optionnel)
        activity_event = None
        if command.activity_id:
            activity_event = ActivityBookedEvent(
                aggregate_id=activity_booking_id,
                trip_id=trip_id,
                user_id=command.user_id,
                activity_name=command.activity_name or "Activité",
                activity_date=command.activity_date or command.depart_date,
                price=command.activity_price or 0.0,
                data={
                    "booking_id": activity_booking_id,
                    "trip_id": trip_id,
                    "user_id": command.user_id,
                    "activity_name": command.activity_name,
                    "activity_date": command.activity_date,
                    "price": command.activity_price
                }
            )
            events_to_append.append(activity_event)
        
        # 7. Sauvegarder les Événements
        try:
            for evt in events_to_append:
                await self.event_store.append(evt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        # 8. Appliquer les Changements d'État
        await self._create_trip_record(trip_id, trip_event)
        await self._create_booking_record(flight_booking_id, flight_event)
        await self._create_booking_record(hotel_booking_id, hotel_event)
        if activity_event:
            await self._create_booking_record(activity_booking_id, activity_event)
            
        return {
            "booking_id": trip_id, # ID du voyage récurrent comme ref principale
            "trip_id": trip_id,
            "event_id": trip_event.event_id,
            "price": command.price,
            "adults": command.adults,
            "created_at": trip_event.timestamp.isoformat(),
            "status": "CONFIRMED",
            "message": "Package réservé avec succès"
        }
    
    # ========================================================================
    # Logique de Validation (Côté Command)
    # ========================================================================
    
    def _validate_booking_command(self, command: BookFlightCommand):
        """
        Valider la commande de réservation.
        
        Règles métier :
        - L'Offer ID doit être valide.
        - La date de départ doit être dans le futur.
        - La date de retour doit être après le départ (si fournie).
        - Le prix doit être positif.
        """
        # Valider les dates
        try:
            depart = datetime.strptime(command.depart_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Format de date de départ invalide"
            )
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if depart < today:
            raise HTTPException(
                status_code=400,
                detail="Impossible de réserver des vols dans le passé"
            )
        
        if command.return_date:
            try:
                return_dt = datetime.strptime(command.return_date, "%Y-%m-%d")
                if return_dt <= depart:
                    raise HTTPException(
                        status_code=400,
                        detail="La date de retour doit être après la date de départ"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Format de date de retour invalide"
                )
        
        # Valider le prix
        if command.price <= 0:
            raise HTTPException(
                status_code=400,
                detail="Le prix doit être positif"
            )

    def _validate_hotel_command(self, command: BookHotelCommand):
        try:
            check_in = datetime.strptime(command.check_in, "%Y-%m-%d")
            check_out = datetime.strptime(command.check_out, "%Y-%m-%d")
        except ValueError:
             raise HTTPException(status_code=400, detail="Date invalide")
             
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if check_in < today:
             raise HTTPException(status_code=400, detail="Le check-in doit être dans le futur")
        
        if check_out <= check_in:
             raise HTTPException(status_code=400, detail="Le check-out doit être après le check-in")
             
    def _validate_package_command(self, command: BookPackageCommand):
        # Réutilisation similaire de logique
        try:
            dep = datetime.strptime(command.depart_date, "%Y-%m-%d")
        except ValueError:
             raise HTTPException(status_code=400, detail="Date invalide")
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if dep < today:
             raise HTTPException(status_code=400, detail="Départ dans le passé")
    
    # ========================================================================
    # Application d'État (Read Model)
    # ========================================================================
    
    async def _create_trip_record(self, trip_id: str, event: TripCreatedEvent) -> Dict:
        """
        Créer l'enregistrement de voyage dans le Read Model.
        """
        from app.auth.db import SessionLocal
        from app.auth.models import Trip
        
        session = SessionLocal()
        try:
            trip = Trip(
                id=trip_id,
                user_id=event.user_id,
                name=event.name,
                total_price=event.total_price,
                currency=event.currency,
                status=event.status
            )
            session.add(trip)
            session.commit()
            return {"id": trip_id}
        except Exception as e:
            session.rollback()
            print(f"Échec de création de l'enregistrement voyage : {e}")
            raise e # Propager l'erreur pour révéler la cause
        finally:
            session.close()

    async def _create_booking_record(
        self, 
        booking_id: str, 
        event: BaseModel 
    ) -> Dict:
        from app.auth.db import SessionLocal
        from app.auth.models import Booking, BookingType, BookingStatus
        
        session = SessionLocal()
        try:
            # Extraire le prix de l'événement - vérifier attribut direct et dict data
            event_price = getattr(event, "price", None)
            if event_price is None and hasattr(event, "data") and isinstance(event.data, dict):
                event_price = event.data.get("price", 0.0)
            if event_price is None:
                event_price = 0.0
            
            # Extraire adultes de la même façon
            event_adults = getattr(event, "adults", None)
            if event_adults is None and hasattr(event, "data") and isinstance(event.data, dict):
                event_adults = event.data.get("adults", 1)
            if event_adults is None:
                event_adults = 1
            
            booking_data = {
                "id": booking_id,
                "trip_id": getattr(event, "trip_id", None),
                "user_id": event.user_id,
                "price": float(event_price),  # Assurer float
                "adults": int(event_adults),  # Assurer int
                "status": BookingStatus.CONFIRMED,
                "event_id": event.event_id,
            }

            if event.event_type == "FlightBooked":
                booking_data.update({
                    "booking_type": BookingType.FLIGHT,
                    "offer_id": event.offer_id,
                    "departure": event.departure,
                    "destination": event.destination,
                    "depart_date": event.depart_date,
                    "return_date": event.return_date,
                })
            elif event.event_type == "HotelBooked":
                booking_data.update({
                    "booking_type": BookingType.HOTEL,
                    "hotel_name": event.hotel_name,
                    "hotel_city": event.hotel_city,
                    "check_in": event.check_in,
                    "check_out": event.check_out,
                })
            elif event.event_type == "ActivityBooked":
                booking_data.update({
                    "booking_type": BookingType.ACTIVITY,
                    "activity_name": event.activity_name,
                    "activity_date": event.activity_date,
                })
            elif event.event_type == "PackageBooked":
                # Support Legacy ou mapping direct package
                 booking_data.update({
                    "booking_type": BookingType.PACKAGE,
                    "offer_id": event.offer_id,
                    "departure": event.departure,
                    "destination": event.destination,
                    "hotel_name": event.hotel_name
                })

            booking = Booking(**booking_data)
            session.add(booking)
            session.commit()
            session.refresh(booking)
            
            return {"id": booking.id}
            
        except Exception as e:
            session.rollback()
            # CRITIQUE : Le Read Model est désynchronisé avec l'Event Store
            logger_msg = f"CRITIQUE : Échec de persistance de réservation {booking_id} vers read model : {e}"
            print(logger_msg)
            raise HTTPException(
                status_code=500, 
                detail=f"Réservation confirmée mais échec mise à jour vue. Référence : {booking_id}. Erreur : {e}"
            )
        finally:
            session.close()
