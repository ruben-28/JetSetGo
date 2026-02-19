from PySide6.QtCore import QObject, Signal
from services.session import SESSION


class HistoryPresenter(QObject):
    """Presenter for HistoryView - handles booking history logic."""
    
    # Signal emitted when user wants to go back to search
    back_to_search = Signal()
    
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        
        # Connect signals
        self.view.back_btn.clicked.connect(self._on_back_clicked)
        
        # Don't load bookings here - wait until view is shown
        # This avoids "User not connected" message at startup
    
    def reload_bookings(self):
        """Public method to reload bookings - call when view is shown."""
        self._load_bookings()
    
    def _load_bookings(self):
        """Load user's booking history from API."""
        if not SESSION.token:
            self.view.set_status("⚠️ Utilisateur non connecté")
            return
        
        self.view.set_status("🔄 Chargement de vos réservations...")
        
        # Call API without user_id (handled by JWT)
        self.api.get_my_bookings_async(
            on_success=self._on_bookings_loaded,
            on_error=self._on_bookings_error
        )
    
    def _on_bookings_loaded(self, bookings: list):
        """Handle successful bookings fetch."""
        self.view.set_bookings(bookings)
        
        if not bookings:
            self.view.set_status("📭 Aucune réservation trouvée")
    
    def _on_bookings_error(self, error):
        """Handle error fetching bookings."""
        self.view.set_status("❌ Erreur de chargement")
        self.view.show_error(f"Impossible de charger vos réservations: {str(error)}")
    
    def _on_back_clicked(self):
        """Handle back button click."""
        self.back_to_search.emit()
