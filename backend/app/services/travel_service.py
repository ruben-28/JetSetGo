# """
# Travel Service Module (DEPRECATED - Facade for CQRS)

# This module is maintained for backward compatibility only.
# All business logic has been moved to CQRS handlers:
# - FlightQueries (app.cqrs.queries.flight_queries) for read operations
# - BookingCommands (app.cqrs.commands.booking_commands) for write operations

# Usage:
#     Prefer using CQRS handlers directly:
#         from app.cqrs import FlightQueries, BookingCommands
    
#     This service is a thin facade that delegates to CQRS handlers.
# """

# from typing import List, Dict, Optional
# from app.gateway import TravelGateway
# from app.cqrs import FlightQueries


# class TravelService:
#     """
#     Service layer for travel operations (DEPRECATED).
    
#     This class is maintained for backward compatibility.
#     It acts as a facade that delegates all operations to CQRS handlers.
    
#     Migration Guide:
#     - For reads: Use FlightQueries directly
#     - For writes: Use BookingCommands directly
    
#     Deprecated: Will be removed in future versions.
#     """
    
#     def __init__(self, gateway: TravelGateway):
#         """
#         Initialize service with gateway dependency.
        
#         Args:
#             gateway: TravelGateway instance for external API calls
#         """
#         self.gateway = gateway
#         # Create CQRS query handler
#         self._queries = FlightQueries(gateway)
    
#     async def search_flights(
#         self,
#         origin: str,
#         destination: str,
#         depart_date: str,
#         return_date: Optional[str] = None,
#         adults: int = 1,
#         budget: Optional[int] = None
#     ) -> List[Dict]:
#         """
#         Search for flight offers (delegates to FlightQueries).
        
#         DEPRECATED: Use FlightQueries.search_flights() directly.
        
#         Args:
#             origin: Departure city/airport
#             destination: Arrival city/airport
#             depart_date: Departure date (YYYY-MM-DD)
#             return_date: Return date (YYYY-MM-DD), optional
#             adults: Number of adult passengers
#             budget: Maximum budget (optional)
        
#         Returns:
#             List of flight offers (filtered and sorted)
#         """
#         # Delegate to CQRS query handler
#         return await self._queries.search_flights(
#             origin=origin,
#             destination=destination,
#             depart_date=depart_date,
#             return_date=return_date,
#             adults=adults,
#             budget=budget
#         )
    
#     async def get_offer_details(self, offer_id: str) -> Dict:
#         """
#         Get detailed information about a specific offer (delegates to FlightQueries).
        
#         DEPRECATED: Use FlightQueries.get_offer_details() directly.
        
#         Args:
#             offer_id: Unique offer identifier
        
#         Returns:
#             Offer details
#         """
#         # Delegate to CQRS query handler
#         return await self._queries.get_offer_details(offer_id)


"""
Travel Service Module
Couche métier pour la gestion des voyages.
Coordonne les appels entre l'API Gateway (Amadeus) et le stockage (si nécessaire).
"""

import logging
from typing import List, Dict, Optional
from app.gateway.travel_provider import TravelProvider

# Configuration du logger
logger = logging.getLogger(__name__)

class TravelService:
    def __init__(self):
        # On instancie le provider qui contient la logique Amadeus
        self.provider = TravelProvider()

    async def search_flights(self, origin: str, destination: str, date: str) -> List[Dict]:
        """
        Recherche des vols en utilisant le provider externe.
        
        Args:
            origin: Code IATA (ex: PAR, TLV, NYC)
            destination: Code IATA (ex: LON, MAD)
            date: YYYY-MM-DD
            
        Returns:
            Liste des offres de vols trouvées
        """
        # Ici, on pourrait ajouter du cache ou de la validation métier supplémentaire
        logger.info(f"Service: Recherche de vol {origin} -> {destination} le {date}")
        
        # Appel au provider réel (Amadeus)
        flights = await self.provider.search_flights(origin, destination, date)
        
        if not flights:
            logger.warning("Aucun vol trouvé via le provider.")
            return []
            
        return flights

    async def search_hotels(self, city_code: str) -> List[Dict]:
        """
        Recherche des hôtels pour une destination donnée.
        """
        logger.info(f"Service: Recherche d'hôtels à {city_code}")
        return await self.provider.search_hotels(city_code)

    async def search_packages(self, origin: str, destination: str, date: str) -> List[Dict]:
        """
        Recherche de packages (Vol + Hôtel).
        Combine les résultats de vols et d'hôtels.
        """
        logger.info(f"Service: Recherche de package {origin} -> {destination} le {date}")
        
        # 1. Rechercher les vols
        flights = await self.search_flights(origin, destination, date)
        if not flights:
            return []
            
        packages = []
        
        # Pour éviter de faire trop d'appels API (quota), on limite à quelques vols
        # En production, on pourrait paralléliser ou cacher les résultats
        for flight in flights[:5]:
            # Dates du vol pour l'hôtel
            check_in_date = flight['depart_date']
            # Si pas de date de retour (aller simple), on assume 3 nuits par défaut pour le package
            # ou on pourrait rejeter les aller-simples pour les packages
            check_out_date = flight.get('return_date')
            if not check_out_date:
                # Calcul date + 3 jours (simplifié)
                from datetime import datetime, timedelta
                try:
                    dt = datetime.strptime(check_in_date, "%Y-%m-%d")
                    check_out_date = (dt + timedelta(days=3)).strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # Recherche d'hôtels correspondants à CE vol
            hotels = await self.provider.search_hotels(destination, check_in_date, check_out_date)
            
            if not hotels:
                continue

            # Créer des packages pour ce vol avec les hôtels trouvés
            # On prend les 3 premiers hôtels pour varier les options
            for hotel in hotels[:3]:
                package = {
                    "type": "package",
                    "id": f"PKG-{flight['id']}-{hotel['id']}",
                    "flight": flight,
                    "hotel": hotel,
                    "total_price": flight['price'] + hotel['price'], # Total vol + hôtel
                    "currency": "EUR"
                }
                packages.append(package)
            
        return packages

    async def get_flight_details(self, offer_id: str) -> Optional[Dict]:
        """
        Récupérer les détails d'un vol spécifique (Simulation pour l'instant).
        Dans un cas réel, Amadeus a un endpoint 'pricing' pour confirmer le prix.
        """
        # Pour ce projet, on peut renvoyer un mock ou stocker les résultats précédents
        return await self.provider.get_offer_details(offer_id)