"""
Travel Provider Module
Intégration avec l'API Amadeus pour obtenir des vols réels.
"""

import os
import logging
from typing import List, Dict, Optional
from amadeus import Client, ResponseError

# Configuration du logger
logger = logging.getLogger(__name__)

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
        # Ici on peut ajouter du code de cleanup si nécessaire
        return False

    def _get_iata_code(self, city_or_code: str) -> str:
        """
        Convertit un nom de ville en code IATA.
        Si c'est déjà un code IATA (3 lettres majuscules), le retourne tel quel.
        
        Args:
            city_or_code: Nom de ville ou code IATA
            
        Returns:
            Code IATA correspondant
        """
        # Si c'est déjà un code IATA (3 lettres), le retourner en majuscules
        if len(city_or_code) == 3 and city_or_code.isalpha():
            return city_or_code.upper()
        
        # Normaliser le nom de ville (minuscules, sans espaces)
        city = city_or_code.lower().strip()
        
        # Mapping des villes principales vers leurs codes IATA
        city_to_iata = {
            # France
            "paris": "CDG",
            "marseille": "MRS",
            "lyon": "LYS",
            "nice": "NCE",
            "toulouse": "TLS",
            "bordeaux": "BOD",
            
            # Israël
            "tel aviv": "TLV",
            "tel-aviv": "TLV",
            "jerusalem": "TLV",  # Utilise TLV (Tel Aviv) comme aéroport principal
            
            # Royaume-Uni
            "london": "LHR",
            "londres": "LHR",
            "manchester": "MAN",
            "edinburgh": "EDI",
            
            # États-Unis
            "new york": "JFK",
            "los angeles": "LAX",
            "san francisco": "SFO",
            "chicago": "ORD",
            "miami": "MIA",
            "boston": "BOS",
            "washington": "DCA",
            
            # Europe
            "berlin": "TXL",
            "rome": "FCO",
            "madrid": "MAD",
            "barcelona": "BCN",
            "amsterdam": "AMS",
            "brussels": "BRU",
            "bruxelles": "BRU",
            "zurich": "ZRH",
            "geneva": "GVA",
            "geneve": "GVA",
            "vienna": "VIE",
            "vienne": "VIE",
            
            # Moyen-Orient
            "dubai": "DXB",
            "doha": "DOH",
            "istanbul": "IST",
            
            # Asie
            "tokyo": "NRT",
            "bangkok": "BKK",
            "singapore": "SIN",
            "hong kong": "HKG",
            "beijing": "PEK",
            "shanghai": "PVG",
        }
        
        # Retourner le code IATA correspondant, ou le texte original en majuscules si non trouvé
        return city_to_iata.get(city, city_or_code.upper())

    async def search_flights(
        self, 
        origin: str, 
        destination: str, 
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> List[Dict]:
        """
        Recherche des vols réels via Amadeus.
        
        Args:
            origin: Code IATA (ex: 'CDG' pour Paris, 'TLV' pour Tel Aviv)
            destination: Code IATA (ex: 'JFK', 'LHR')
            depart_date: Date de départ au format 'YYYY-MM-DD'
            return_date: Date de retour au format 'YYYY-MM-DD' (optionnel)
            adults: Nombre d'adultes (par défaut 1)
            
        Returns:
            Liste de dictionnaires représentant les vols simplifiés.
        """
        if not self.client:
            logger.error("Client Amadeus non initialisé.")
            return []

        try:
            # Convertir les noms de villes en codes IATA
            origin_iata = self._get_iata_code(origin)
            destination_iata = self._get_iata_code(destination)
            
            logger.info(f"Recherche Amadeus: {origin} ({origin_iata}) -> {destination} ({destination_iata}) le {depart_date}")
            logger.debug(f"Paramètres de recherche: origin={origin_iata}, destination={destination_iata}, date={depart_date}, adults={adults}")
            
            # Appel API officiel
            response = self.client.shopping.flight_offers_search.get(
                originLocationCode=origin_iata,
                destinationLocationCode=destination_iata,
                departureDate=depart_date,
                adults=adults,
                max=10  # Limite à 10 résultats pour être rapide
            )
            
            logger.debug(f"Réponse Amadeus reçue: {len(response.data)} offres trouvées")
            
            # Parser les résultats en passant les dates pour le contexte
            parsed_flights = self._parse_flights(response.data, depart_date, return_date)
            logger.info(f"Recherche terminée: {len(parsed_flights)} vols parsés avec succès")
            
            return parsed_flights

        except ResponseError as error:
            logger.error(f"Erreur API Amadeus: {error}")
            logger.error(f"Détails de l'erreur: {error.response.body if hasattr(error, 'response') else 'N/A'}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []

    def _parse_flights(self, offers: List, depart_date: str, return_date: Optional[str]) -> List[Dict]:
        """
        Convertit la réponse complexe d'Amadeus en format OfferOut.
        
        Args:
            offers: Liste d'offres Amadeus
            depart_date: Date de départ pour inclure dans la réponse
            return_date: Date de retour pour inclure dans la réponse
            
        Returns:
            Liste de dictionnaires conformes au modèle OfferOut
        """
        results = []
        
        for offer in offers:
            try:
                # On prend le premier itinéraire (aller simple ou aller du premier segment)
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                first_segment = segments[0]
                last_segment = segments[-1]
                
                # Calcul du nombre d'escales (nombre de segments - 1)
                stops = len(segments) - 1
                
                # Conversion de la durée ISO8601 en minutes (ex: "PT4H45M" -> 285)
                duration_min = self._parse_duration_to_minutes(itinerary['duration'])
                
                # Récupération du prix et conversion en int (arrondi)
                price = int(float(offer['price']['total']))
                
                # Calcul d'un score basé sur le prix et la durée
                # Score plus bas = meilleur (combinaison prix/durée normalisée)
                score = (price / 100) + (duration_min / 60)
                
                # Construction de l'offre au format attendu
                flight_data = {
                    "id": offer['id'],  # Utiliser 'id' au lieu de 'offer_id'
                    "departure": first_segment['departure']['iataCode'],
                    "destination": last_segment['arrival']['iataCode'],
                    "depart_date": depart_date,
                    "return_date": return_date or "",
                    "airline": self._get_airline_name(first_segment['carrierCode']),
                    "price": price,  # Int comme attendu
                    "duration_min": duration_min,
                    "stops": stops,
                    "score": round(score, 2),
                    "adults": 1,  # Par défaut
                    "mock": False  # Données réelles d'Amadeus
                }
                results.append(flight_data)
                
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Impossible de parser l'offre {offer.get('id', 'unknown')}: {e}")
                continue
                
        return results

    async def get_offer_details(self, offer_id: str) -> dict:
        """
        Récupère les détails d'une offre spécifique.
        
        Args:
            offer_id: ID de l'offre à détailler
            
        Returns:
            Dictionnaire contenant les détails de l'offre
        """
        if not self.client:
            logger.warning("Client Amadeus non initialisé. Retour de détails mock.")
            return self._get_mock_offer_details(offer_id)
        
        try:
            logger.info(f"Récupération des détails pour l'offre: {offer_id}")
            
            # Note: Amadeus ne fournit pas d'endpoint direct pour les détails d'offre
            # par ID. En production, on devrait:
            # 1. Stocker les offres complètes en cache/base de données
            # 2. Ou recréer la recherche pour obtenir l'offre
            # Pour l'instant, on retourne des détails enrichis basés sur l'ID
            
            # Retourner des détails enrichis (mock pour l'instant)
            return self._get_mock_offer_details(offer_id)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails: {e}")
            return self._get_mock_offer_details(offer_id)
    
    def _get_mock_offer_details(self, offer_id: str) -> dict:
        """
        Genere des details d'offre mock.
        
        Args:
            offer_id: ID de l'offre
            
        Returns:
            Details d'offre mock
        """
        return {
            "id": offer_id,
            "baggage": "1 bagage en cabine (10kg) + 1 bagage en soute (23kg)",
            "refund_policy": "Remboursable jusqu'a 24h avant le depart (frais de 50 euros)",
            "notes": "Vol opere par un partenaire de la compagnie. Enregistrement en ligne disponible 24h avant le depart.",
            "hotel_suggestion": {
                "name": "Hotel Central",
                "price": 89,
                "rating": 4.2,
                "distance_from_airport": "15 minutes"
            },
            "mock": True
        }
    
    def _parse_duration_to_minutes(self, duration_iso: str) -> int:
        """
        Convertit une durée ISO8601 en minutes.
        
        Args:
            duration_iso: Durée au format ISO8601 (ex: "PT4H45M")
            
        Returns:
            Durée en minutes
        """
        import re
        
        # Enlever le préfixe 'PT'
        duration = duration_iso.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        # Extract heures si présentes
        hours_match = re.search(r'(\d+)H', duration)
        if hours_match:
            hours = int(hours_match.group(1))
        
        # Extract minutes si présentes
        minutes_match = re.search(r'(\d+)M', duration)
        if minutes_match:
            minutes = int(minutes_match.group(1))
        
        return (hours * 60) + minutes

    def _get_airline_name(self, code: str) -> str:
        """Helper pour donner un nom lisible (dictionnaire simplifié)."""
        # Dans un vrai projet, on utiliserait l'endpoint 'airline-code-lookup' d'Amadeus
        # Pour l'instant, on mappe les codes les plus courants pour l'affichage
        airlines = {
            "AF": "Air France",
            "LY": "El Al",
            "U2": "EasyJet",
            "BA": "British Airways",
            "LH": "Lufthansa",
            "DL": "Delta Airlines",
            "AA": "American Airlines",
            "EK": "Emirates",
            "RK": "Ryanair"
        }
        return airlines.get(code, code)
    
    async def search_hotels(self, city_code: str) -> List[Dict]:
        """
        Recherche des hotels dans une ville via Amadeus.
        
        Processus en 2 etapes (plan gratuit Amadeus):
        1. Recuperer les IDs d'hotels dans la ville
        2. Recuperer les offres pour ces hotels
        
        Args:
            city_code: Code IATA de la ville (ex: 'LON' pour Londres, 'PAR' pour Paris)
            
        Returns:
            Liste de dictionnaires contenant les informations d'hotels
        """
        if not self.client:
            logger.error("Client Amadeus non initialise.")
            return []
        
        try:
            logger.info(f"Recherche d'hotels a {city_code}")
            
            # Etape 1: Recuperer les IDs d'hotels dans la ville
            logger.debug(f"Etape 1: Recuperation des IDs d'hotels pour {city_code}")
            hotels_response = self.client.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            
            if not hotels_response.data:
                logger.warning(f"Aucun hotel trouve pour {city_code}")
                return []
            
            # Prendre les 5 premiers hotel IDs
            hotel_ids = [hotel['hotelId'] for hotel in hotels_response.data[:5]]
            logger.debug(f"Hotels IDs recuperes: {hotel_ids}")
            
            # Etape 2: Recuperer les offres pour ces hotels
            logger.debug(f"Etape 2: Recuperation des offres pour {len(hotel_ids)} hotels")
            offers_response = self.client.shopping.hotel_offers_search.get(
                hotelIds=','.join(hotel_ids)
            )
            
            if not offers_response.data:
                logger.warning(f"Aucune offre trouvee pour les hotels de {city_code}")
                return []
            
            # Parser les resultats
            hotels = self._parse_hotels(offers_response.data)
            logger.info(f"Recherche terminee: {len(hotels)} hotels avec offres trouve(s)")
            
            return hotels
            
        except ResponseError as error:
            logger.error(f"Erreur API Amadeus: {error}")
            logger.error(f"Details de l'erreur: {error.response.body if hasattr(error, 'response') else 'N/A'}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la recherche d'hotels: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _parse_hotels(self, offers: List) -> List[Dict]:
        """
        Convertit la reponse Amadeus en format standardise.
        
        Args:
            offers: Liste d'offres d'hotels Amadeus
            
        Returns:
            Liste de dictionnaires avec infos hotels
        """
        results = []
        
        for offer in offers:
            try:
                hotel = offer.get('hotel', {})
                
                # Recuperer la premiere offre disponible
                first_offer = offer.get('offers', [{}])[0]
                price_info = first_offer.get('price', {})
                
                # Extraire les informations
                hotel_data = {
                    "id": offer.get('id', hotel.get('hotelId', 'unknown')),
                    "name": hotel.get('name', 'Hotel sans nom'),
                    "city": hotel.get('cityCode', 'N/A'),
                    "price": float(price_info.get('total', 0)),
                    "currency": price_info.get('currency', 'EUR'),
                    "description": hotel.get('description', {}).get('text', 'Pas de description disponible'),
                    "rating": hotel.get('rating', 0)
                }
                
                results.append(hotel_data)
                
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Impossible de parser l'offre hotel {offer.get('id', 'unknown')}: {e}")
                continue
        
        return results
