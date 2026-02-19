import os
import sys
# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.ai.assistant_orchestrator import AssistantOrchestrator

async def test_prompt_generation():
    # Patch OllamaGateway where it is used in the orchestrator file
    with patch("app.ai.assistant_orchestrator.OllamaGateway") as MockGateway:
        # Setup the mock to behave like a context manager
        mock_gateway_instance = MockGateway.return_value
        mock_gateway_instance.__aenter__.return_value = mock_gateway_instance
        mock_gateway_instance.chat_completion = AsyncMock(return_value={"content": "Mock Response"})
        
        orchestrator = AssistantOrchestrator()
        
        # Test 1: General Conversation about Safety
        print("\n--- Test 1: General (Safety) ---")
        await orchestrator._handle_general_conversation("Je veux savoir si c'est dangereux d'aller en Iran")
        
        # Access the arguments passed to chat_completion
        call_args = mock_gateway_instance.chat_completion.call_args
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
        
        call_args = mock_gateway_instance.chat_completion.call_args
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
