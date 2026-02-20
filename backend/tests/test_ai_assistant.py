
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.ai.assistant_orchestrator import AssistantOrchestrator

@pytest.fixture
def orchestrator():
    return AssistantOrchestrator()

@pytest.mark.asyncio
async def test_extract_preferences_beach(orchestrator):
    message = "Je veux aller à la plage en juin"
    preferences = orchestrator._extract_preferences(message)
    assert "plage" in preferences

@pytest.mark.asyncio
async def test_extract_preferences_multiple(orchestrator):
    message = "Vacances pas cher en famille à la montagne"
    preferences = orchestrator._extract_preferences(message)
    assert "pas cher" in preferences
    assert "famille" in preferences
    assert "montagne" in preferences

@pytest.mark.asyncio
async def test_extract_preferences_empty(orchestrator):
    message = "Je veux partir quelque part"
    preferences = orchestrator._extract_preferences(message)
    assert preferences == []

@pytest.mark.asyncio
async def test_analyze_intent_structure(orchestrator):
    # Mocking external calls
    with patch("app.ai.assistant_orchestrator.HuggingFaceGateway") as MockHF:
        mock_hf_instance = AsyncMock()
        MockHF.return_value.__aenter__.return_value = mock_hf_instance
        
        # Mock classify_intent
        mock_hf_instance.classify_intent.return_value = {
            "intent": "inspiration",
            "confidence": 0.95
        }
        
        # Mock extract_entities
        mock_hf_instance.extract_entities.return_value = []
        
        message = "Conseils pour la plage en été"
        
        analysis = await orchestrator._analyze_intent(message)
        
        
        assert analysis["intent"] == "inspiration"
        assert "plage" in analysis["entities"]["preferences"]


