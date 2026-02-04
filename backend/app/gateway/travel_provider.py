"""
Travel Provider Module
Intégration avec l'API Amadeus pour obtenir des vols réels.
"""

import os
import logging
import re
from typing import List, Dict, Optional
from functools import lru_cache
from amadeus import Client, ResponseError

# Configuration du logger
logger = logging.getLogger(__name__)

# Cache global pour les recherches de lieux (évite les appels API répétés)
@lru_cache(maxsize=128)
def _cached_location_search(api_key, api_secret, keyword):
    """
    Fonction de recherche cachée. 
    Nécessite les clés en arguments pour être indépendante de l'instance.
    """
    try:
        client = Client(client_id=api_key, client_secret=api_secret)
        response = client.reference_data.locations.get(
            keyword=keyword,
            subType=['CITY', 'AIRPORT']
        )
        return response.data
    except Exception as e:
        logger.error(f"Erreur cache location search: {e}")
        return []

class TravelProvider:
    """
    Gateway vers l'API Amadeus pour récupérer les offres de vols réelles.
    """
    
    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        self.client = None

        if self.api_key and self.api_secret:
            try:
                self.client = Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret
                )
                logger.info("Connecté à l'API Amadeus avec succès.")
            except Exception as e:
                logger.error(f"Échec de l'initialisation Amadeus: {e}")
        else:
            logger.warning("Clés API Amadeus manquantes. Le provider ne fonctionnera pas.")

    async def __aenter__(self):
        """Support pour async with context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup lors de la sortie du context manager"""
        return False

    def _get_iata_code(self, city_or_code: str) -> str:
        """Convertit un nom de ville en code IATA."""
        if len(city_or_code) == 3 and city_or_code.isalpha():
            return city_or_code.upper()
        
        city = city_or_code.lower().strip()
        
        city_to_iata = {
            "paris": "CDG", "marseille": "MRS", "lyon": "LYS", "nice": "NCE",
            "toulouse": "TLS", "bordeaux": "BOD", "tel aviv": "TLV", "tel-aviv": "TLV",
            "jerusalem": "TLV", "london": "LHR", "londres": "LHR", "manchester": "MAN",
            "edinburgh": "EDI", "new york": "JFK", "los angeles": "LAX", "san francisco": "SFO",
            "chicago": "ORD", "miami": "MIA", "boston": "BOS", "washington": "DCA",
            "berlin": "TXL", "rome": "FCO", "madrid": "MAD", "barcelona": "BCN",
            "amsterdam": "AMS", "brussels": "BRU", "bruxelles": "BRU", "zurich": "ZRH",
            "geneva": "GVA", "geneve": "GVA", "vienna": "VIE", "vienne": "VIE",
            "dubai": "DXB", "doha": "DOH", "istanbul": "IST", "tokyo": "NRT",
            "bangkok": "BKK", "singapore": "SIN", "hong kong": "HKG", "beijing": "PEK",
            "shanghai": "PVG",
        }
        
        return city_to_iata.get(city, city_or_code.upper())

    async def search_locations(self, keyword: str) -> List[Dict]:
        """Recherche des villes et aéroports (Autocomplete)."""
        if not self.api_key or not self.api_secret:
            logger.error("Clés API manquantes.")
            return []
            
        try:
            logger.info(f"Recherche de lieux pour: {keyword}")
            data = _cached_location_search(self.api_key, self.api_secret, keyword)
            
            results = []
            for loc in data:
                code = loc.get('iataCode')
                name = loc.get('name')
                country = loc.get('address', {}).get('countryCode', '')
                subtype = loc.get('subType')
                
                label = f"{name} ({code}) - {country}"
                
                results.append({
                    "label": label,
                    "iata": code,
                    "name": name,
                    "country": country,
                    "type": subtype
                })
            
            return results
        except Exception as e:
            logger.error(f"Erreur inattendue locations: {e}")
            return []

    async def _resolve_city_code(self, keyword: str) -> str:
        """Tente de résoudre un nom de ville en code IATA via l'API."""
        locations = await self.search_locations(keyword)
        if locations:
             code = locations[0].get('iata') # Fixed: search_locations returns 'iata' key, not 'code'
             logger.info(f"Résolu '{keyword}' -> {code}")
             return code
        return keyword

    async def search_flights(self, origin: str, destination: str, depart_date: str, return_date: Optional[str] = None, adults: int = 1, budget: Optional[int] = None) -> List[Dict]:
        """Recherche des vols réels via Amadeus."""
        if not self.client:
            logger.error("Client Amadeus non initialisé.")
            return []

        try:
            origin_iata = self._get_iata_code(origin)
            destination_iata = self._get_iata_code(destination)
            
            if len(origin_iata) != 3:
                origin_iata = await self._resolve_city_code(origin)
            if len(destination_iata) != 3:
                destination_iata = await self._resolve_city_code(destination)

            logger.info(f"Recherche Amadeus: {origin} ({origin_iata}) -> {destination} ({destination_iata}) le {depart_date}")
            
            # Paramètres de base
            params = {
                'originLocationCode': origin_iata,
                'destinationLocationCode': destination_iata,
                'departureDate': depart_date,
                'adults': adults,
                'max': 10
            }
            if return_date:
                params['returnDate'] = return_date
            if budget:
                params['maxPrice'] = int(budget)

            response = self.client.shopping.flight_offers_search.get(**params)
            
            parsed_flights = self._parse_flights(response.data, depart_date, return_date)
            return parsed_flights

        except ResponseError as error:
            logger.error(f"Erreur API Amadeus: {error}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche: {e}")
            return []

    def _parse_flights(self, offers: List, depart_date: str, return_date: Optional[str]) -> List[Dict]:
        """Convertit la réponse Amadeus en format OfferOut."""
        results = []
        for offer in offers:
            try:
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                stops = len(segments) - 1
                duration_min = self._parse_duration_to_minutes(itinerary['duration'])
                price = int(float(offer['price']['total']))
                score = (price / 100) + (duration_min / 60)
                
                flight_data = {
                    "id": offer['id'],
                    "departure": first_segment['departure']['iataCode'],
                    "destination": last_segment['arrival']['iataCode'],
                    "depart_date": depart_date,
                    "return_date": return_date or "",
                    "airline": self._get_airline_name(first_segment['carrierCode']),
                    "price": price,
                    "duration_min": duration_min,
                    "stops": stops,
                    "score": round(score, 2),
                    "adults": 1,
                    "mock": False
                }
                results.append(flight_data)
            except Exception as e:
                logger.warning(f"Impossible de parser l'offre: {e}")
                continue
        return results

    async def get_offer_details(self, offer_id: str) -> dict:
        """Récupère les détails d'une offre."""
        # Note: Sans cache d'objet, on retourne un placeholder car Amadeus exige l'objet complet pour le pricing
        return {
            "id": offer_id,
            "notes": "Détails temps réel non disponibles sans cache offre.",
            "price_verified": False,
            "real_time_data": True,
            "baggage": "Standard (1x23kg)", # Placeholder safest bet
            "refund_policy": "Non remboursable", # Placeholder safest bet
            "hotel_suggestion": {"name": "Hôtel Partenaire (Non spécifié)"}
        }

    def _parse_duration_to_minutes(self, duration_iso: str) -> int:
        """Convertit PT4H45M en minutes."""
        duration = duration_iso.replace('PT', '')
        hours = 0
        minutes = 0
        
        hours_match = re.search(r'(\d+)H', duration)
        if hours_match:
            hours = int(hours_match.group(1))
            
        minutes_match = re.search(r'(\d+)M', duration)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            
        return (hours * 60) + minutes

    def _get_airline_name(self, code: str) -> str:
        """Dictionnaire simplifié des compagnies."""
        airlines = {
            "AF": "Air France", "LY": "El Al", "U2": "EasyJet", "BA": "British Airways",
            "LH": "Lufthansa", "DL": "Delta", "AA": "American Airlines", "EK": "Emirates",
            "RK": "Ryanair", "TO": "Transavia"
        }
        return airlines.get(code, code)

    async def search_hotels(self, city_code: str, check_in: str = None, check_out: str = None) -> List[Dict]:
        """Recherche des hotels via Amadeus."""
        if not self.client: return []
        try:
            hotels_response = self.client.reference_data.locations.hotels.by_city.get(cityCode=city_code)
            if not hotels_response.data: return []
            
            hotel_ids = [hotel['hotelId'] for hotel in hotels_response.data[:10]]
            
            params = {'hotelIds': ','.join(hotel_ids), 'adults': 1, 'roomQuantity': 1, 'currency': 'EUR'}
            if check_in: params['checkInDate'] = check_in
            if check_out: params['checkOutDate'] = check_out
                
            offers_response = self.client.shopping.hotel_offers_search.get(**params)
            return self._parse_hotels(offers_response.data) if offers_response.data else []
        except Exception as e:
            logger.error(f"Erreur recherche hotels: {e}")
            return []

    def _parse_hotels(self, offers: List) -> List[Dict]:
        """Convertit la réponse hôtel."""
        results = []
        for offer in offers:
            try:
                hotel = offer.get('hotel', {})
                first_offer = offer.get('offers', [{}])[0]
                price_info = first_offer.get('price', {})
                
                results.append({
                    "id": offer.get('id', hotel.get('hotelId', 'unknown')),
                    "name": hotel.get('name', 'Hotel sans nom'),
                    "city": hotel.get('cityCode', 'N/A'),
                    "price": float(price_info.get('total', 0)),
                    "currency": price_info.get('currency', 'EUR'),
                    "description": hotel.get('description', {}).get('text', 'Pas de description'),
                    "rating": hotel.get('rating', 0)
                })
            except Exception:
                continue
        return results

    async def search_cities(self, keyword: str) -> List[Dict]:
        """
        Recherche de villes/aéroports via Amadeus Location API.
        Utilisé pour l'autocomplete dans l'UI.
        
        Args:
            keyword: Mot-clé de recherche (ex: "Par" pour Paris)
            
        Returns:
            Liste de dictionnaires contenant:
            - name: Nom de la ville/aéroport
            - iata_code: Code IATA (3 lettres)
            - country: Pays
            - type: 'CITY' ou 'AIRPORT'
        """
        if not self.client:
            logger.error("Client Amadeus non initialisé.")
            return []
        
        if not keyword or len(keyword) < 2:
            logger.warning("Mot-clé trop court pour la recherche (min 2 caractères)")
            return []
        
        try:
            logger.info(f"Recherche de villes/aéroports pour: '{keyword}'")
            
            # Appel Amadeus Location API
            response = self.client.reference_data.locations.get(
                keyword=keyword,
                subType='CITY,AIRPORT'
            )
            
            if not response.data:
                logger.info(f"Aucun résultat pour '{keyword}'")
                return []
            
            # Parser les résultats
            results = []
            for location in response.data[:10]:  # Limiter à 10 résultats
                try:
                    result = {
                        "name": location.get('name', 'Unknown'),
                        "iata_code": location.get('iataCode', ''),
                        "country": location.get('address', {}).get('countryName', 'Unknown'),
                        "type": location.get('subType', 'CITY'),
                        "city_name": location.get('address', {}).get('cityName', '')
                    }
                    results.append(result)
                except (KeyError, AttributeError) as e:
                    logger.warning(f"Erreur lors du parsing d'une location: {e}")
                    continue
            
            logger.info(f"Recherche terminée: {len(results)} résultat(s) trouvé(s)")
            return results
            
        except ResponseError as error:
            logger.error(f"Erreur API Amadeus: {error}")
            logger.error(f"Détails de l'erreur: {error.response.body if hasattr(error, 'response') else 'N/A'}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche de villes: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []
