import asyncio
import os
from app.gateway.huggingface_gateway import HuggingFaceGateway

async def test_intents():
    output_file = "test_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("--- Test de Classification d'Intention Hugging Face (V2 - MoritzLaurer Model) ---\n")
        
        gateway = HuggingFaceGateway()
        
        test_phrases = [
            "Je veux aller à Paris demain", # Flight
            "Trouve moi un hotel à New York", # Hotel
            "Des idées pour des vacances en été ?", # Inspiration
            "Montre moi mes réservations", # History
            "C'est cher la vie au Japon ?", # Budget
            "Bonjour, comment tu vas ?", # General
            "Je veux un remboursement", # Should trigger fallback/general
            "Rembourse moi mon billet" # Should be General
        ]
        
        f.write(f"Mode Mock: {gateway.is_mock_mode()}\n")
        
        for phrase in test_phrases:
            f.write(f"\nPhrase: '{phrase}'\n")
            try:
                result = await gateway.classify_intent(phrase)
                
                intent = result['intent']
                confidence = result['confidence']
                
                f.write(f" -> Intention: {intent}\n")
                f.write(f" -> Confiance: {confidence:.4f}\n")
                
            except Exception as e:
                f.write(f"ERREUR: {e}\n")

        await gateway.close()

if __name__ == "__main__":
    asyncio.run(test_intents())
