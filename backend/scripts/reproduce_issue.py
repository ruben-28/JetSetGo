
import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.ai.assistant_orchestrator import AssistantOrchestrator

async def reproduce():
    orchestrator = AssistantOrchestrator()
    user_message = "ma question tu me conseils de partir ou en vacances en juin a la plage"
    
    print(f"User Message: {user_message}")
    
    # Analyze intent and entities to see what is extracted
    analysis = await orchestrator._analyze_intent(user_message)
    print("\n--- Analysis Result ---")
    print(f"Intent: {analysis['intent']}")
    print(f"Entities: {analysis['entities']}")
    
    if analysis['intent'] == 'inspiration':
        context = {
            "period": analysis['entities'].get("period"),
            "preferences": analysis['entities'].get("preferences", []),
            "message": user_message
        }
        
        # This will call _generate_ollama_response which now has print statements
        print("\n--- Running Process Message ---")
        try:
            result = await orchestrator.process_message(user_message, 123)
            # The result itself contain the response text
            # print(f"Response: {result['response_text']}")
        except Exception as e:
            print(f"Error calling Ollama: {e}")

if __name__ == "__main__":
    asyncio.run(reproduce())
