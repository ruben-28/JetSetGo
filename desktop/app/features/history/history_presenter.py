from PySide6.QtCore import QObject, Signal
from services.session import SESSION


class HistoryPresenter(QObject):
    """Présenteur pour HistoryView - gère la logique de l'historique des réservations."""
    
    # Signal émis lorsque l'utilisateur veut retourner à la recherche
    back_to_search = Signal()
    
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        
        # Connecter les signaux
        self.view.back_btn.clicked.connect(self._on_back_clicked)
        
        # Ne pas charger les réservations ici - attendre que la vue soit affichée
        # Cela évite le message "Utilisateur non connecté" au démarrage
    
    def reload_bookings(self):
        """Méthode publique pour recharger les réservations - appeler quand la vue est affichée."""
        self._load_bookings()
    
    def _load_bookings(self):
        """Charge l'historique des réservations de l'utilisateur depuis l'API."""
        if not SESSION.token:
            self.view.set_status("⚠️ Utilisateur non connecté")
            return
        
        self.view.set_status("🔄 Chargement de vos réservations...")
        
        # Appeler l'API sans user_id (géré par JWT)
        self.api.get_my_bookings_async(
            on_success=self._on_bookings_loaded,
            on_error=self._on_bookings_error
        )
    
    def _on_bookings_loaded(self, bookings: list):
        """Gère le succès de la récupération des réservations."""
        self.view.set_bookings(bookings)
        
        if not bookings:
            self.view.set_status("📭 Aucune réservation trouvée")
    
    def _on_bookings_error(self, error):
        """Gère l'erreur de récupération des réservations."""
        self.view.set_status("❌ Erreur de chargement")
        self.view.show_error(f"Impossible de charger vos réservations: {str(error)}")
    
    def _on_back_clicked(self):
        """Gère le clic sur le bouton retour."""
        self.back_to_search.emit()
