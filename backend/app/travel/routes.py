"""
Fichier: backend/app/travel/routes.py
Objectif: Endpoints HTTP pour les opérations de voyage (Vols, Hôtels, Séjours).
Architecture: Pattern CQRS (Command Query Responsibility Segregation).

Implémentation CQRS:
- Requêtes (GET) -> FlightQueries / TripQueries (Lecture seule).
- Commandes (POST) -> BookingCommands / SearchCommands (Écriture / Actions complexes).
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.gateway import TravelProvider
from app.services.travel_service import TravelService
from app.cqrs import FlightQueries, BookingCommands
from app.cqrs.commands.booking_commands import BookFlightCommand, BookHotelCommand, BookPackageCommand
from app.cqrs.commands.search_commands import SearchCommands, SearchPackageCommand
from app.cqrs.queries.trip_queries import TripQueries
from app.auth.dependencies import get_current_user
from app.auth.models import User


# ============================================================================
# Configuration du Routeur
# ============================================================================

router = APIRouter(prefix="/travel", tags=["travel"])


# ============================================================================
# Injection de Dépendances (Pattern CQRS)
# ============================================================================

async def get_flight_queries():
    """
    Factory pour FlightQueries (Côté Query CQRS).
    Crée une instance de gateway et le gestionnaire de requêtes avec nettoyage approprié.
    Utilisé pour toutes les opérations de LECTURE (READ).
    """
    async with TravelProvider() as gateway:
        yield FlightQueries(gateway)


async def get_booking_commands():
    """
    Factory pour BookingCommands (Côté Command CQRS).
    Crée le gestionnaire de commandes.
    Utilisé pour toutes les opérations d'ÉCRITURE (WRITE).
    """
    yield BookingCommands()


async def get_search_commands():
    """Factory de dépendance pour SearchCommands."""
    yield SearchCommands()


async def get_trip_queries():
    """Factory de dépendance pour TripQueries."""
    yield TripQueries()


# ============================================================================
# Modèles de Réponse (Response Models)
# ============================================================================

class OfferOut(BaseModel):
    """Modèle de réponse pour une offre de vol."""
    id: str
    departure: str
    destination: str
    depart_date: str
    return_date: str
    airline: str
    price: int
    duration_min: int
    stops: int
    score: float
    adults: int = Field(default=1)
    mock: bool = Field(default=False)


class OfferDetailsOut(BaseModel):
    """Modèle de réponse pour les détails d'une offre."""
    id: str
    baggage: str
    refund_policy: str
    notes: str
    hotel_suggestion: dict
    mock: bool = Field(default=False)


class BookingOut(BaseModel):
    """Modèle de confirmation de réservation."""
    booking_id: str
    trip_id: Optional[str] = None  # Ajouté pour référence voyage
    event_id: str
    status: str
    price: float
    adults: int
    created_at: str
    message: str
    
    # Champs optionnels selon le type
    offer_id: Optional[str] = None
    departure: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None


class LocationOut(BaseModel):
    """Modèle de réponse pour la recherche de lieux."""
    name: str
    code: str
    type: str  # CITY ou AIRPORT
    detail: str


# ============================================================================
# Endpoints de Requête (Opérations de Lecture - CQRS Query Side)
# ============================================================================

@router.get("/search", response_model=List[OfferOut])
async def search(
    departure: str = Query(..., min_length=2, description="Ville/Aéroport de départ"),
    destination: str = Query(..., min_length=2, description="Ville/Aéroport de destination"),
    depart_date: str = Query(..., description="Date de départ (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Date de retour (YYYY-MM-DD)"),
    budget: Optional[int] = Query(None, ge=0, description="Budget maximum"),
    max_stops: Optional[int] = Query(None, ge=0, le=5, description="Max escales (0=direct, 1=max 1 escale, None=tous)"),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Recherche d'offres de vol (QUERY - Lecture).
    
    Pattern CQRS : Cet endpoint utilise FlightQueries pour les opérations en lecture seule.
    Aucun modification d'état, seulement récupération et filtrage.
    
    Paramètres :
    - departure : Code IATA départ
    - destination : Code IATA destination
    - depart_date : Date départ
    - return_date : Date retour
    - budget : Budget max (optionnel)
    - max_stops : Nombre max d'escales
    
    Retourne :
    - Liste d'offres triées par prix.
    """
    try:
        offers = await queries.search_flights(
            origin=departure,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=1,  # Défaut à 1 pour compatibilité
            budget=budget,
            max_stops=max_stops
        )
        return offers
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec de la recherche : {str(e)}")


@router.get("/details/{offer_id}", response_model=OfferDetailsOut)
async def details(
    offer_id: str,
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Obtenir les détails d'une offre spécifique (QUERY - Lecture).
    """
    try:
        details = await queries.get_offer_details(offer_id)
        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec récupération détails : {str(e)}")


# ============================================================================
# Endpoints de Commande (Opérations d'Écriture - CQRS Command Side)
# ============================================================================

@router.post("/book")  # Removed response_model for consistency
async def book_flight(
    command: BookFlightCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Réserver un vol (COMMAND - Écriture avec Event Sourcing).
    
    Flux Event Sourcing :
    1. Valide la commande de réservation.
    2. Génère un FlightBookedEvent.
    3. Persiste l'événement dans l'Events Store EN PREMIER.
    4. Applique le changement d'état (crée le booking).
    5. Retourne la confirmation.
    """
    try:
        # Force l'ID utilisateur depuis le token
        command.user_id = current_user.id
        result = await commands.book_flight(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec réservation vol : {str(e)}")


@router.post("/book/hotel")
async def book_hotel(
    command: BookHotelCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Réserver un hôtel (COMMAND - Écriture).
    """
    try:
        command.user_id = current_user.id
        result = await commands.book_hotel(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec réservation hôtel : {str(e)}")


@router.post("/book/package")
async def book_package(
    command: BookPackageCommand,
    current_user: User = Depends(get_current_user),
    commands: BookingCommands = Depends(get_booking_commands)
):
    """
    Réserver un package Vol + Hôtel (COMMAND - Écriture).
    """
    try:
        command.user_id = current_user.id
        result = await commands.book_package(command)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec réservation package : {str(e)}")


# ============================================================================
# Endpoint Mes Réservations (Read Model Query)
# ============================================================================

class UserBookingOut(BaseModel):
    """Modèle de réponse réservation utilisateur."""
    id: str
    booking_type: str
    price: float
    adults: int
    status: str
    created_at: Optional[str]
    event_id: str
    
    # Flight fields
    offer_id: Optional[str] = None
    departure: Optional[str] = None
    destination: Optional[str] = None
    depart_date: Optional[str] = None
    return_date: Optional[str] = None
    
    # Hotel/Package fields
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None

# ============================================================================
# Recherche Villes/Aéroports (Autocomplete)
# ============================================================================

@router.get("/cities/search")
async def search_cities(
    keyword: str = Query(..., min_length=2, description="Mot-clé (min 2 chars)"),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Recherche de villes et aéroports (Autocomplete).
    Utilisé pour obtenir les codes IATA.
    """
    try:
        # Utilise la gateway via FlightQueries
        async with TravelProvider() as gateway:
            results = await gateway.search_cities(keyword)
            return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec recherche ville : {str(e)}")


# ============================================================================
# Nouveaux Endpoints Packages et Hôtels
# ============================================================================

@router.get("/hotels")
async def search_hotels(
    city_code: str = Query(..., min_length=3, description="Code IATA ou nom ville")
):
    """
    Chercher des hôtels dans une ville spécifique.
    """
    try:
        service = TravelService()
        return await service.search_hotels(city_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec recherche hôtel : {str(e)}")


@router.post("/packages/search")
async def search_packages_post(
    command: SearchPackageCommand,
    commands: SearchCommands = Depends(get_search_commands)
):
    """
    Chercher des packages combinés Vol + Hôtel.
    """
    try:
        return await commands.search_packages(command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec recherche package : {str(e)}")


@router.get("/trips/me")
async def get_my_trips(
    current_user: User = Depends(get_current_user),
    queries: TripQueries = Depends(get_trip_queries)
):
    """
    Récupérer tous les voyages (dossiers) de l'utilisateur courant.
    """
    try:
        return queries.get_user_trips(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec récupération voyages : {str(e)}")


@router.get("/trips/{trip_id}")
async def get_trip_details(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    queries: TripQueries = Depends(get_trip_queries)
):
    """
    Récupérer le détail d'un voyage (incluant toutes les réservations).
    """
    try:
        trip = queries.get_trip_details(trip_id, current_user.id)
        if not trip:
            raise HTTPException(status_code=404, detail="Voyage non trouvé")
        return trip
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec récupération détails voyage : {str(e)}")


@router.get("/my-bookings", response_model=List[UserBookingOut])
async def get_my_bookings(
    current_user: User = Depends(get_current_user),
    queries: FlightQueries = Depends(get_flight_queries)
):
    """
    Récupérer toutes les réservations de l'utilisateur connecté.
    Utilise le token JWT pour identifier l'utilisateur.
    """
    try:
        return await queries.get_user_bookings(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec récupération réservations : {str(e)}")


@router.get("/locations", response_model=List[LocationOut])
async def get_locations(
    keyword: str = Query(..., min_length=2, description="Mot-clé (ex: 'Lon', 'Par')")
):
    """
    Autocomplete pour aéroports et villes.
    Utilisez ce endpoint pour obtenir les codes IATA officiels.
    """
    try:
        async with TravelProvider() as provider:
            return await provider.search_locations(keyword)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Échec recherche lieux : {str(e)}")
