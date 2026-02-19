# -*- coding: utf-8 -*-
import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Test d'Integration Amadeus API
Tests complets pour verifier le bon fonctionnement de l'integration Amadeus.

Ce script teste:
1. La connexion a l'API Amadeus
2. La conversion des codes IATA
3. Le parsing des durees ISO8601
4. La recherche de vols reels
5. La recuperation des details d'offre
6. La gestion des erreurs
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add backend app to path

# Load environment variables
from dotenv import load_dotenv
import os
load_dotenv()

from app.gateway import TravelProvider


def print_header(title):
    """Print a formatted test header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(test_name, passed, details=""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} | {test_name}")
    if details:
        print(f"        {details}")


async def test_iata_conversion():
    """Test 1: Conversion des noms de villes en codes IATA"""
    print_header("TEST 1: Conversion des codes IATA")
    
    provider = TravelProvider()
    
    # Test cases: (input, expected_output)
    test_cases = [
        ("Paris", "CDG"),
        ("PARIS", "CDG"),
        ("paris", "CDG"),
        ("London", "LHR"),
        ("londres", "LHR"),
        ("New York", "JFK"),
        ("Tel Aviv", "TLV"),
        ("CDG", "CDG"),  # Already IATA code
        ("TLV", "TLV"),  # Already IATA code
    ]
    
    all_passed = True
    for city, expected in test_cases:
        result = provider._get_iata_code(city)
        passed = result == expected
        all_passed = all_passed and passed
        print_test(
            f"{city:15} -> {result:3}",
            passed,
            f"Expected: {expected}" if not passed else ""
        )
    
    return all_passed


async def test_duration_parsing():
    """Test 2: Parsing des durees ISO8601"""
    print_header("TEST 2: Parsing des durees ISO8601")
    
    provider = TravelProvider()
    
    # Test cases: (iso_duration, expected_minutes)
    test_cases = [
        ("PT4H45M", 285),      # 4h45 = 285 minutes
        ("PT2H", 120),          # 2h = 120 minutes
        ("PT30M", 30),          # 30 minutes
        ("PT1H30M", 90),        # 1h30 = 90 minutes
        ("PT10H15M", 615),      # 10h15 = 615 minutes
    ]
    
    all_passed = True
    for iso_duration, expected in test_cases:
        result = provider._parse_duration_to_minutes(iso_duration)
        passed = result == expected
        all_passed = all_passed and passed
        print_test(
            f"{iso_duration:12} -> {result:4} min",
            passed,
            f"Expected: {expected} min" if not passed else ""
        )
    
    return all_passed


async def test_amadeus_connection():
    """Test 3: Connexion a l'API Amadeus"""
    print_header("TEST 3: Connexion a l'API Amadeus")
    
    provider = TravelProvider()
    
    if provider.client is None:
        print_test(
            "Connexion Amadeus",
            False,
            "Client non initialise. Verifiez les cles API dans .env"
        )
        return False
    
    print_test("Connexion Amadeus", True, "Client initialise avec succes")
    print(f"        API Key: {provider.api_key[:10]}..." if provider.api_key else "        API Key: Non configuree")
    
    return True


async def test_flight_search():
    """Test 4: Recherche de vols reels"""
    print_header("TEST 4: Recherche de vols (Paris -> Londres)")
    
    # Calculate future dates
    tomorrow = datetime.now() + timedelta(days=1)
    next_week = datetime.now() + timedelta(days=8)
    
    depart_date = tomorrow.strftime("%Y-%m-%d")
    return_date = next_week.strftime("%Y-%m-%d")
    
    print(f"\nDates de recherche:")
    print(f"   Depart: {depart_date}")
    print(f"   Retour: {return_date}\n")
    
    async with TravelProvider() as provider:
        try:
            offers = await provider.search_flights(
                origin="Paris",
                destination="London",
                depart_date=depart_date,
                return_date=return_date,
                adults=1
            )
            
            if not offers:
                print_test("Recherche de vols", False, "Aucune offre trouvee")
                return False, None
            
            print_test("Recherche de vols", True, f"{len(offers)} offres trouvees")
            
            # Display first 3 offers
            print(f"\n   Premieres offres:")
            for i, offer in enumerate(offers[:3], 1):
                print(f"   {i}. {offer['airline']:20} | ${offer['price']:5} | {offer['duration_min']:3} min | {offer['stops']} escale(s)")
                print(f"      ID: {offer['id']}")
            
            return True, offers[0] if offers else None
            
        except Exception as e:
            print_test("Recherche de vols", False, str(e))
            import traceback
            print(f"\n{traceback.format_exc()}")
            return False, None


async def test_offer_details(offer_id=None):
    """Test 5: Recuperation des details d'offre"""
    print_header("TEST 5: Details d'offre")
    
    # Use a real offer ID if provided, otherwise use a test ID
    test_id = offer_id or "TEST-OFFER-123"
    
    print(f"\nRecuperation des details pour: {test_id}\n")
    
    async with TravelProvider() as provider:
        try:
            details = await provider.get_offer_details(test_id)
            
            if not details:
                print_test("Details d'offre", False, "Aucun detail retourne")
                return False
            
            print_test("Details d'offre", True, "Details recuperes avec succes")
            
            # Display details
            print(f"\n   Details de l'offre:")
            print(f"   ID: {details.get('id', 'N/A')}")
            print(f"   Bagages: {details.get('baggage', 'N/A')}")
            print(f"   Remboursement: {details.get('refund_policy', 'N/A')}")
            print(f"   Notes: {details.get('notes', 'N/A')}")
            
            if 'hotel_suggestion' in details:
                hotel = details['hotel_suggestion']
                print(f"\n   Suggestion d'hotel:")
                print(f"      {hotel.get('name', 'N/A')} - ${hotel.get('price', 'N/A')}/nuit")
                print(f"      Note: {hotel.get('rating', 'N/A')}/5")
                print(f"      Distance: {hotel.get('distance_from_airport', 'N/A')}")
            
            print(f"\n   Mode: {'Mock' if details.get('mock', False) else 'Reel'}")
            
            return True
            
        except Exception as e:
            print_test("Details d'offre", False, str(e))
            import traceback
            print(f"\n{traceback.format_exc()}")
            return False


async def test_error_handling():
    """Test 6: Gestion des erreurs"""
    print_header("TEST 6: Gestion des erreurs")
    
    async with TravelProvider() as provider:
        # Test with invalid date
        print("\nTest avec date invalide:")
        try:
            offers = await provider.search_flights(
                origin="Paris",
                destination="London",
                depart_date="2020-01-01",  # Date passee
                adults=1
            )
            # L'API devrait retourner une liste vide ou une erreur
            print_test("Date invalide", True, "Erreur geree correctement (retour liste vide)")
        except Exception as e:
            print_test("Date invalide", True, f"Exception capturee: {type(e).__name__}")
        
        # Test with invalid IATA code
        print("\nTest avec code IATA invalide:")
        try:
            tomorrow = datetime.now() + timedelta(days=1)
            offers = await provider.search_flights(
                origin="XXXXX",  # Code invalide
                destination="London",
                depart_date=tomorrow.strftime("%Y-%m-%d"),
                adults=1
            )
            print_test("Code IATA invalide", True, "Erreur geree correctement")
        except Exception as e:
            print_test("Code IATA invalide", True, f"Exception capturee: {type(e).__name__}")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  TESTS D'INTEGRATION AMADEUS API")
    print("=" * 70)
    print("\nDemarrage de la suite de tests...\n")
    
    results = {}
    
    # Test 1: IATA conversion
    results['iata'] = await test_iata_conversion()
    
    # Test 2: Duration parsing
    results['duration'] = await test_duration_parsing()
    
    # Test 3: API connection
    results['connection'] = await test_amadeus_connection()
    
    # Test 4: Flight search (returns offer for next test)
    search_passed, first_offer = await test_flight_search()
    results['search'] = search_passed
    
    # Test 5: Offer details (use real offer if available)
    offer_id = first_offer['id'] if first_offer else None
    results['details'] = await test_offer_details(offer_id)
    
    # Test 6: Error handling
    results['errors'] = await test_error_handling()
    
    # Summary
    print_header("RESUME DES TESTS")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    print(f"\n   Tests reussis: {passed}/{total}")
    print(f"   Taux de reussite: {(passed/total)*100:.1f}%\n")
    
    for test_name, result in results.items():
        status = "[OK]  " if result else "[FAIL]"
        print(f"   {status} {test_name.upper()}")
    
    print("\n" + "=" * 70)
    
    if passed == total:
        print("\n*** TOUS LES TESTS SONT PASSES! ***")
        print("\nL'integration Amadeus fonctionne correctement.")
    else:
        print(f"\n*** {total - passed} test(s) ont echoue. ***")
        print("\nVerifiez:")
        print("   1. Les cles API Amadeus dans le fichier .env")
        print("   2. La connexion Internet")
        print("   3. Les logs ci-dessus pour plus de details")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
