"""
Assistant Presenter Module
Business logic for AI consultation interface.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class AssistantPresenter(QObject):
    """
    Presenter for AI Assistant view.
    
    Responsibilities:
    - Handle user interactions
    - Manage API calls to consultation endpoint
    - Update view with responses
    - Handle demo mode indicators
    - Manage conversation history
    """
    
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api_client = api_client
        self.last_response = ""  # For copy function
        
        # Connect view signals
        self.view.send_requested.connect(self.on_send_message)
        self.view.copy_requested.connect(self.on_copy_response)
        self.view.new_conversation_requested.connect(self.on_new_conversation)
    
    def on_send_message(self, mode: str, message: str):
        """Handle send message request"""
        # Validate length client-side (redundant with backend but good UX)
        if len(message) > 8000:
            self.view.show_error("Message trop long (max 8000 caractères)")
            return
        
        # Build context from cached data (if any)
        context = self._build_context()
        
        # Add user message to UI immediately
        self.view.add_user_message(message)
        self.view.clear_status()
        
        # Show loading
        self.view.set_loading(True)
        
        # API call
        self.api_client.consult_ai_async(
            mode=mode,
            message=message,
            context=context,
            on_success=self.on_success,
            on_error=self.on_error
        )
    
    def on_success(self, response):
        """Handle successful LLM response"""
        self.view.set_loading(False)
        
        # Check if mock mode
        meta = response.get("meta", {})
        if meta.get("mock", False):
            reason = meta.get("reason", "service_unavailable")
            self.view.show_demo_banner(reason)
        else:
            self.view.hide_demo_banner()
        
        # Add AI response to conversation
        answer = response.get("answer", "Pas de réponse")
        model = response.get("model", "unknown")
        self.view.add_ai_message(answer, model)
        
        # Store for copy function
        self.last_response = answer
    
    def on_error(self, error):
        """Handle API error"""
        self.view.set_loading(False)
        self.view.show_error(f"Erreur: {str(error)}")
    
    def on_copy_response(self):
        """Copy last AI response to clipboard"""
        if self.last_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response)
            self.view.show_success("Réponse copiée!")
    
    def on_new_conversation(self):
        """Clear conversation and reset"""
        self.view.clear_conversation()
        self.last_response = ""
        self.view.show_success("Nouvelle conversation démarrée")
    
    def _build_context(self) -> dict:
        """
        Build context dict with proper DTOs.
        Retrieves cached context from session/navigation if available.
        
        Returns a valid ConsultContext structure.
        """
        # For now, return empty but valid ConsultContext
        # This will be populated when navigating from SearchView with offers
        return {
            "selected_offers": None,  # Will be list of OfferDTO dicts when set
            "booking_info": None,     # Will be BookingDTO dict when set
            "budget_max": None,       # Will be int when set
            "user_prefs": {}          # Always a dict
        }
    
    def set_initial_context(self, mode: str, context: dict):
        """
        Set initial context when navigating from another view.
        
        Args:
            mode: Pre-selected mode (compare, budget, policy, free)
            context: Pre-filled context (offers, booking, etc.)
        """
        # Map mode to selector index
        mode_index_map = {
            "compare": 0,
            "budget": 1,
            "policy": 2,
            "free": 3
        }
        
        if mode in mode_index_map:
            self.view.set_mode(mode_index_map[mode])
        
        # Store context for next API call
        # This would be used by _build_context()
        # TODO: Store in instance variable or session
