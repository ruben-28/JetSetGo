# -*- coding: utf-8 -*-
import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test de Recherche d'Hotels via Amadeus API
Test simple pour verifier la fonctionnalite de recherche d'hotels.
"""

import asyncio
import sys
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Ajouter le chemin du backend

from app.gateway import TravelProvider


async def test_hotel_search():
    """Test de recherche d'hotels a Londres"""
    
    print("\n" + "=" * 70)
    print("  TEST: Recherche d'Hotels a Londres (LON)")
    print("=" * 70 + "\n")
    
    # Instancier le provider
    async with TravelProvider() as provider:
        # Verifier que le client est initialise
        if not provider.client:
            print("[ERREUR] Client Amadeus non initialise.")
            print("Verifiez que AMADEUS_CLIENT_ID et AMADEUS_CLIENT_SECRET sont dans .env\n")
            return
        
        print("[OK] Client Amadeus initialise\n")
        
        # Lancer la recherche sur Londres
        print("Recherche d'hotels a Londres (LON)...\n")
        hotels = await provider.search_hotels("LON")
        
        if not hotels:
            print("[ATTENTION] Aucun hotel trouve.\n")
            return
        
        # Afficher les resultats
        print(f"[OK] {len(hotels)} hotel(s) trouve(s)\n")
        print("-" * 70)
        
        for i, hotel in enumerate(hotels, 1):
            print(f"\n{i}. {hotel['name']}")
            print(f"   Prix: {hotel['price']} {hotel['currency']}")
            print(f"   Etoiles: {hotel['rating']}")
            print(f"   Ville: {hotel['city']}")
            if hotel['description']:
                # Limiter la description a 100 caracteres
                desc = hotel['description'][:100]
                if len(hotel['description']) > 100:
                    desc += "..."
                print(f"   Description: {desc}")
        
        print("\n" + "=" * 70)
        print(f"\nTest termine avec succes! {len(hotels)} hotel(s) affiche(s).\n")


async def test_multiple_cities():
    """Test de recherche sur plusieurs villes"""
    
    print("\n" + "=" * 70)
    print("  TEST: Recherche d'Hotels dans Plusieurs Villes")
    print("=" * 70 + "\n")
    
    cities = [
        ("LON", "Londres"),
        ("PAR", "Paris"),
        ("NYC", "New York")
    ]
    
    async with TravelProvider() as provider:
        if not provider.client:
            print("[ERREUR] Client Amadeus non initialise.\n")
            return
        
        results = {}
        
        for code, name in cities:
            print(f"Recherche a {name} ({code})...")
            hotels = await provider.search_hotels(code)
            results[name] = len(hotels)
            print(f"  -> {len(hotels)} hotel(s) trouve(s)\n")
        
        # Afficher le resume
        print("-" * 70)
        print("\nResume:")
        for city, count in results.items():
            print(f"  {city}: {count} hotel(s)")
        
        print("\n" + "=" * 70 + "\n")


async def main():
    """Execute tous les tests"""
    
    print("\n" + "=" * 70)
    print("  TESTS DE RECHERCHE D'HOTELS - AMADEUS API")
    print("=" * 70)
    
    # Test 1: Recherche simple sur Londres
    await test_hotel_search()
    
    # Test 2: Recherche sur plusieurs villes (optionnel)
    # Decommentez pour tester plusieurs villes
    # await test_multiple_cities()
    
    print("\nTous les tests sont termines!\n")


if __name__ == "__main__":
    asyncio.run(main())
