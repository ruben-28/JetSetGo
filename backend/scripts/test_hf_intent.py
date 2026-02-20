
import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.gateway.huggingface_gateway import HuggingFaceGateway

async def test_intent():
    gateway = HuggingFaceGateway()
    
    sentences = [
        "tu me conseils de partir ou en mars",
        "ou aller en vacances",
        "donne moi des idées de voyage",
        "je veux partir a la plage"
    ]
    
    print("--- Testing HF Intent Classification ---")
    try:
        if gateway.is_mock_mode():
            print("WARNING: Running in MOCK MODE")
        else:
            print("Running in REAL MODE with HF API")
            
        for sentence in sentences:
            print(f"\nAnalyzing: '{sentence}'")
            try:
                result = await gateway.classify_intent(sentence)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Gateway Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_intent())
