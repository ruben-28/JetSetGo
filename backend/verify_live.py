
import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.append("c:/Users/ethan/OneDrive/Bureau/JetSetGo/backend")

from app.ai.assistant_orchestrator import AssistantOrchestrator

async def main():
    print("Initializing Orchestrator...")
    orchestrator = AssistantOrchestrator()
    
    user_message = "je veux savoir si cest conseille de partir en iran"
    print(f"\nUser Query: {user_message}")
    print("-" * 50)
    
    # We call the inspiration handler directly to test that specific path logic
    # First we need to simulate the entity extraction that would happen
    entities = orchestrator._analyze_intent(user_message)["entities"]
    
    # Now call the handler
    response = await orchestrator._handle_inspiration(entities, user_message)
    
    print("\nAI Response:")
    print(response["response_text"])
    print("-" * 50)
    
    with open("backend/verify_log.txt", "w", encoding="utf-8") as f:
        f.write(response["response_text"])

if __name__ == "__main__":
    asyncio.run(main())
