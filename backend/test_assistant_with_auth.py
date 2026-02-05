# -*- coding: utf-8 -*-
"""
Script de test complet pour l'assistant IA
1. Login pour obtenir un token JWT
2. Appel à l'endpoint assistant
"""
import httpx
import asyncio
import getpass


async def test_assistant():
    """Test complet avec authentification"""
    base_url = "http://localhost:8000"
    
    # Étape 1: Login
    print("[1] Connexion au backend...")
    username = input("Nom d'utilisateur ou email: ")
    password = getpass.getpass("Mot de passe: ")
    
    try:
        async with httpx.AsyncClient() as client:
            # Login
            login_response = await client.post(
                f"{base_url}/auth/login",
                json={
                    "username_or_email": username,
                    "password": password
                },
                timeout=10.0
            )
            
            if login_response.status_code != 200:
                print(f"[ERREUR] Login echoue: {login_response.status_code}")
                print(login_response.text)
                return
            
            token = login_response.json()["access_token"]
            print("[OK] Connexion reussie! Token obtenu.")
            
            # Étape 2: Test assistant
            print("\n[2] Test de l'assistant IA...")
            message = input("Message a envoyer (ou Entree pour 'Bonjour'): ").strip()
            if not message:
                message = "Bonjour"
            
            assistant_response = await client.post(
                f"{base_url}/api/ai/assistant",
                json={"message": message},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if assistant_response.status_code != 200:
                print(f"[ERREUR] Assistant echoue: {assistant_response.status_code}")
                print(assistant_response.text)
                return
            
            result = assistant_response.json()
            
            # Affichage des résultats
            print("\n" + "=" * 60)
            print("[SUCCESS] Reponse de l'assistant:")
            print("=" * 60)
            print(f"Action       : {result.get('action')}")
            print(f"Vue cible    : {result.get('target_view')}")
            print(f"Prefill data : {result.get('prefill_data')}")
            print(f"\nReponse texte:")
            print(result.get('response_text', ''))
            print("\nMetadata     :", result.get('metadata'))
            print("=" * 60)
            
            # Test navigation
            if result.get('action') == 'navigate':
                print(f"\n[INFO] L'assistant demande de naviguer vers: {result.get('target_view')}")
                print(f"       Avec donnees: {result.get('prefill_data')}")
            
            return result
            
    except httpx.ConnectError:
        print("[ERREUR] Impossible de se connecter au backend.")
        print("Verifiez que le backend tourne: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"[ERREUR] {type(e).__name__}: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   TEST DE L'ASSISTANT IA (avec authentification)")
    print("=" * 60)
    print("\nAssurez-vous que le backend tourne:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")
    print("")
    
    asyncio.run(test_assistant())
