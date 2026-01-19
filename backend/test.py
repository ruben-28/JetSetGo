from app.gateway.travel_provider import TravelProvider
from dotenv import load_dotenv

# Charge les variables d'env
load_dotenv()

provider = TravelProvider()
# Test: Tel Aviv (TLV) -> Paris (CDG) pour dans 2 mois (ajuste la date !)
vols = provider.search_flights("TLV", "CDG", "2026-03-01")

print(f"Trouvé {len(vols)} vols !")
for vol in vols:
    print(f"- {vol['airline']} : {vol['price']} {vol['currency']}")