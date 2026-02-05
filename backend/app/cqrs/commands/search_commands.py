from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import asyncio
import logging

from app.gateway.travel_provider import TravelProvider

logger = logging.getLogger(__name__)

class SearchPackageCommand(BaseModel):
    """
    Command to search for packages (Flight + Hotel + Activities).
    """
    origin: str
    destination: str
    depart_date: str
    return_date: str
    adults: int = 1
    
    # Optional filters
    budget: Optional[int] = None
    hotel_stars: Optional[int] = None
    include_activities: bool = False

class SearchCommands:
    """
    Handler for Search-related commands (Aggregator).
    """
    
    def __init__(self):
        self.provider = TravelProvider()
        
    async def search_packages(self, command: SearchPackageCommand) -> Dict:
        """
        Aggregates search results from Flight and Hotel providers.
        """
        try:
            # 1. Resolve Location Codes
            # We need to know the destination details (lat/long) for activities
            # But Amadeus Search Flights uses IATA codes.
            
            # Parallel Execution: Flight and Hotel Search
            # Hotel search needs city code. Flight needs airpots. Usually they match or are related.
            
            logger.info(f"Searching packages for {command.destination}")
            
            # Run Flight and Hotel search in parallel
            # Hotels are searched by City Code (Destination IATA)
            
            # Note: We don't have lat/long easily here without an extra call.
            # We'll use the destination IATA for hotel search.
            
            flight_task = self.provider.search_flights(
                origin=command.origin,
                destination=command.destination,
                depart_date=command.depart_date,
                return_date=command.return_date,
                adults=command.adults,
                budget=command.budget
            )
            
            hotel_task = self.provider.search_hotels(
                 city_code=command.destination, # Assuming input is IATA for now, or provider resolves it
                 check_in=command.depart_date,
                 check_out=command.return_date
            )
            
            flights, hotels = await asyncio.gather(flight_task, hotel_task)
            
            # Activities (Optional and requires Lat/Long - usually we'd get this from the city search)
            # For this MVP, we might skip or do a separate lookup if needed.
            activities = []
            if command.include_activities:
                # We need coordinates. Let's do a quick hack or separate call if we had time.
                # For now, returning empty or mocking if we can't get coords easily.
                pass

            # Aggregate Results
            # Simple Strategy: Return top 5 flights and top 5 hotels independently for the user to mix/match
            # OR create pre-bundled combinations.
            
            # Let's return them as lists for the frontend to combine.
            
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
            logger.error(f"Error searching packages: {e}")
            return {"flights": [], "hotels": [], "error": str(e)}
