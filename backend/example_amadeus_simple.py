
"""
Exemple d'utilisation simple du service Amadeus Airline Code Lookup
Pour tester rapidement la fonctionnalité sans lancer tout le serveur FastAPI.
"""

import asyncio
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Import du service
from app.services.amadeus_service import AmadeusService


async def main():
    """
    Exemple simple d'utilisation du service Amadeus.
    """
    print("🛫 Exemple d'utilisation du service Amadeus Airline Lookup\n")
    
    # Vérifier que les credentials sont configurés
    if not os.getenv("AMADEUS_CLIENT_ID") or not os.getenv("AMADEUS_CLIENT_SECRET"):
        print("❌ ERREUR : Les variables d'environnement AMADEUS_CLIENT_ID et AMADEUS_CLIENT_SECRET ne sont pas définies.")
        print("\nVeuillez les ajouter dans votre fichier .env :")
        print("AMADEUS_CLIENT_ID=votre_client_id")
        print("AMADEUS_CLIENT_SECRET=votre_client_secret")
        return
    
    try:
        # Créer une instance du service
        service = AmadeusService()
        
        # Exemple 1: Rechercher Air France
        print("Recherche de la compagnie 'AF' (Air France)...")
        airline = await service.get_airline_by_code("AF")
        
        print(f"""
✅ Compagnie trouvée :
   Code IATA  : {airline['iataCode']}
   Code ICAO  : {airline['icaoCode']}
   Nom        : {airline['commonName']}
   Nom legal  : {airline['businessName']}
""")
        
        # Exemple 2: Rechercher une autre compagnie
        print("\nRecherche de la compagnie 'BA' (British Airways)...")
        airline2 = await service.get_airline_by_code("BA")
        print(f"✅ {airline2['commonName']} trouvée !\n")
        
        # Exemple 3: Gestion d'erreur
        print("Test avec un code invalide 'ZZ'...")
        try:
            await service.get_airline_by_code("ZZ")
        except ValueError as e:
            print(f"✅ Erreur gérée correctement : {e}\n")
        
        print("✨ Tous les exemples ont fonctionné avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
