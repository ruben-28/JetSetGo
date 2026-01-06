from typing import List, Dict
import random
from datetime import datetime, timedelta

class TravelProviderGateway:
    """
    Gateway vers un service externe de voyage.
    Pour l’instant : mock stable (facile à présenter). Plus tard : vraie API.
    """

    def search_offers(self, destination: str, depart_date: str, return_date: str, budget: int) -> List[Dict]:
        random.seed(f"{destination}-{depart_date}-{return_date}-{budget}")  # stable par recherche

        airlines = ["ElAl", "Air France", "Lufthansa", "Ryanair", "Turkish"]
        offers = []

        base_price = max(80, budget // 2) if budget else 300
        for i in range(10):
            price = base_price + random.randint(-40, 250)
            duration = random.randint(180, 720)  # minutes
            stops = random.choice([0, 0, 1, 1, 2])

            offer_id = f"{destination[:3].upper()}-{depart_date.replace('-','')}-{i}"

            offers.append({
                "id": offer_id,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
                "airline": random.choice(airlines),
                "price": max(50, price),
                "duration_min": duration,
                "stops": stops,
                "score": round(random.uniform(3.2, 4.9), 1),
            })

        # filtrage budget si donné
        if budget:
            offers = [o for o in offers if o["price"] <= budget]

        # tri prix
        offers.sort(key=lambda x: x["price"])
        return offers

    def get_details(self, offer_id: str) -> Dict:
        # détails mock basés sur l'id
        return {
            "id": offer_id,
            "baggage": "Cabin + 20kg",
            "refund_policy": "Refund partiel jusqu’à 48h avant",
            "notes": "Offre générée (mock). Remplacer par API réelle plus tard.",
            "hotel_suggestion": {
                "name": "City Center Hotel",
                "stars": 4,
                "night_price": 120
            }
        }
