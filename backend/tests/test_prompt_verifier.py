
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.ai.assistant_orchestrator import AssistantOrchestrator

async def test_prompt_generation():
    orchestrator = AssistantOrchestrator()
    # Mock the gateway to avoid actual API calls
    orchestrator.ollama.chat_completion = AsyncMock(return_value={"content": "Mock Response"})
    
    # Test 1: General Conversation about Safety
    print("\n--- Test 1: General (Safety) ---")
    await orchestrator._handle_general_conversation("Je veux savoir si c'est dangereux d'aller en Iran")
    
    # Access the arguments passed to chat_completion
    call_args = orchestrator.ollama.chat_completion.call_args
    if call_args:
        messages = call_args.kwargs['messages']
        system_msg = messages[0]['content']
        user_msg = messages[1]['content']
        print(f"System Message: {system_msg}")
        print(f"User Message: {user_msg}")
        
        if "équilibré et objectif" in system_msg and "risques éventuels" in user_msg:
            print("✅ General Safety Prompt: PASS")
        else:
            print("❌ General Safety Prompt: FAIL")

    # Test 2: Inspiration Request (Specific Country)
    print("\n--- Test 2: Inspiration (Specific Country) ---")
    # Simulate extraction results that might occur
    await orchestrator._handle_inspiration(
        {"period": "mai", "preferences": [], "destination": "Iran"}, 
        "Est-ce que l'Iran est une bonne idée ?"
    )
    
    call_args = orchestrator.ollama.chat_completion.call_args
    if call_args:
        messages = call_args.kwargs['messages']
        user_msg = messages[1]['content']
        print(f"User Message: {user_msg}")
        
        if "Si la demande concerne un pays spécifique" in user_msg and "NE PAS utiliser le format liste" in user_msg:
            print("✅ Inspiration Context Prompt: PASS")
        else:
            print("❌ Inspiration Context Prompt: FAIL")

if __name__ == "__main__":
    asyncio.run(test_prompt_generation())
