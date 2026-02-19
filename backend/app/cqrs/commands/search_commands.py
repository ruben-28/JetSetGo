"""
Fichier: backend/app/cqrs/commands/search_commands.py
Objectif: Commandes de recherche pour les packages.
"""

from typing import Dict, Optional
from pydantic import BaseModel
import asyncio
import logging

from app.gateway.travel_provider import TravelProvider

logger = logging.getLogger(__name__)

class SearchPackageCommand(BaseModel):
    """
    Commande pour rechercher des packages (Vol + Hôtel + Activités).
    """
    origin: str
    destination: str
    depart_date: str
    return_date: str
    adults: int = 1
    
    # Filtres optionnels
    budget: Optional[int] = None
    hotel_stars: Optional[int] = None
    include_activities: bool = False

class SearchCommands:
    """
    Gestionnaire pour les commandes liées à la recherche (Agrégateur).
    """
    
    def __init__(self):
        self.provider = TravelProvider()
        
    async def search_packages(self, command: SearchPackageCommand) -> Dict:
        """
        Agrège les résultats de recherche des fournisseurs de Vols et d'Hôtels.
        """
        try:
            # 1. Résolution des Codes Lieux
            # Nous devons connaître les détails de la destination (lat/long) pour les activités.
            # Mais Amadeus Search Flights utilise des codes IATA.
            
            # Exécution Parallèle : Recherche Vol et Hôtel
            # La recherche d'hôtel nécessite un code ville. La recherche de vol nécessite des aéroports.
            # Habituellement, ils correspondent ou sont liés.
            
            logger.info(f"Recherche de packages pour {command.destination}")
            
            # Lancer les recherches Vol et Hôtel en parallèle
            # Les hôtels sont recherchés par Code Ville (IATA Destination)
            
            # Note: Nous n'avons pas facilement la lat/long ici sans appel supplémentaire.
            # Nous utiliserons l'IATA de destination pour la recherche d'hôtel.
            
            flight_task = self.provider.search_flights(
                origin=command.origin,
                destination=command.destination,
                depart_date=command.depart_date,
                return_date=command.return_date,
                adults=command.adults,
                budget=command.budget
            )
            
            hotel_task = self.provider.search_hotels(
                 city_code=command.destination, # Supposons que l'entrée est IATA pour l'instant
                 check_in=command.depart_date,
                 check_out=command.return_date
            )
            
            flights, hotels = await asyncio.gather(flight_task, hotel_task)
            
            # Activités (Optionnel et nécessite Lat/Long - nous l'aurions normalement de la recherche ville)
            # Pour ce MVP, nous pourrions sauter ou faire une recherche séparée si nécessaire.
            activities = []
            if command.include_activities:
                # Nous avons besoin de coordonnées. 
                # Pour l'instant, retourne vide ou mock si nous ne pouvons pas obtenir les coords facilement.
                pass

            # Agrégation des Résultats
            # Stratégie Simple : Retourner le top 5 vols et top 5 hôtels indépendamment pour que le frontend les combine
            # OU créer des combinaisons pré-groupées.
            
            # Retournons-les sous forme de listes pour que le frontend les combine.
            
            return {
                "flights": flights[:10],
                "hotels": hotels[:10],
                "activities": activities,
                "metadata": {
                    "count_flights": len(flights),
                    "count_hotels": len(hotels)
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de packages : {e}")
            return {"flights": [], "hotels": [], "error": str(e)}
