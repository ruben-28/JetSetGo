# -*- coding: utf-8 -*-
"""
Script de test pour verifier la connexion a Ollama dans Docker
Usage: python test_ollama_connection.py
"""
import httpx
import asyncio
import os
import sys


async def test_connection():
    """Test de connexion a Ollama avec diagnostics detailles"""
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"[*] Test de connexion a Ollama")
    print(f"    URL: {url}")
    print("-" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test 1: API tags (liste des modeles)
            print("\n[1] Test 1: Recuperation des modeles disponibles...")
            response = await client.get(f"{url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                if models:
                    print(f"[OK] Ollama accessible! {len(models)} modele(s) disponible(s):")
                    for model in models:
                        print(f"   - {model['name']}")
                    
                    # Test 2: Verifier si qwen2.5:3b est disponible
                    print("\n[2] Test 2: Verification du modele qwen2.5:3b...")
                    has_qwen = any("qwen2.5:3b" in m["name"] for m in models)
                    
                    if has_qwen:
                        print("[OK] Modele qwen2.5:3b trouve!")
                        
                        # Test 3: Generer une reponse de test
                        print("\n[3] Test 3: Test de generation de texte...")
                        test_payload = {
                            "model": "qwen2.5:3b",
                            "messages": [
                                {"role": "user", "content": "Dis bonjour en une phrase."}
                            ],
                            "stream": False
                        }
                        
                        response = await client.post(
                            f"{url}/api/chat",
                            json=test_payload,
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            message = result.get("message", {}).get("content", "")
                            print(f"[OK] Generation reussie!")
                            print(f"   Reponse: {message[:100]}...")
                            
                            print("\n" + "=" * 60)
                            print("[SUCCESS] TOUS LES TESTS REUSSIS!")
                            print("   L'assistant IA devrait fonctionner correctement.")
                            print("=" * 60)
                            return True
                        else:
                            print(f"[ERREUR] Generation echouee: HTTP {response.status_code}")
                            print(f"   {response.text[:200]}")
                    else:
                        print("[ATTENTION] Modele qwen2.5:3b non trouve!")
                        print("\nSolution: Telecharger le modele dans le conteneur Docker:")
                        print("   docker exec -it ollama ollama pull qwen2.5:3b")
                        return False
                else:
                    print("[ATTENTION] Aucun modele installe dans Ollama")
                    print("\nSolution: Installer un modele:")
                    print("   docker exec -it ollama ollama pull qwen2.5:3b")
                    return False
            else:
                print(f"[ERREUR] Reponse HTTP {response.status_code}")
                print(f"   {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print(f"[ERREUR] Erreur de connexion: {e}")
        print("\nSuggestions:")
        print("   1. Verifiez que le conteneur Docker est en cours d'execution:")
        print("      docker ps | findstr ollama")
        print("   2. Verifiez que le port est bien mappe:")
        print("      docker port ollama")
        print("   3. Essayez de redemarrer le conteneur:")
        print("      docker restart ollama")
        return False
    
    except httpx.TimeoutException:
        print("[ERREUR] Timeout: Ollama met trop de temps a repondre")
        print("\nLe conteneur est peut-etre surcharge. Verifiez les logs:")
        print("   docker logs ollama")
        return False
    
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   DIAGNOSTIC DE CONNEXION OLLAMA (Docker)")
    print("=" * 60)
    
    success = asyncio.run(test_connection())
    
    if not success:
        print("\n" + "=" * 60)
        print("[ECHEC] TEST ECHOUE")
        print("   Consultez les suggestions ci-dessus.")
        print("=" * 60)
        sys.exit(1)
    
    sys.exit(0)
