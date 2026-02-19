"""
Module Assistant Presenter
Logique métier pour l'interface de l'assistant IA avec support de navigation.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


class AssistantPresenter(QObject):
    """
    Présenteur pour la vue Assistant IA.
    
    Responsabilités :
    - Gérer les interactions utilisateur
    - Gérer les appels API vers le endpoint de l'assistant
    - Gérer les actions de navigation (vols, hôtels, packages)
    - Mettre à jour la vue avec les réponses
    - Gérer l'historique de conversation
    """
    
    # Signaux de navigation
    navigate_to_flights = Signal(dict)  # {destination, travelers}
    navigate_to_hotels = Signal(dict)   # {destination}
    navigate_to_packages = Signal(dict)  # {destination}
    navigate_to_history = Signal(dict)   # {}
    
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api_client = api_client
        self.last_response = ""  # Pour la fonction copier
        
        # Connecter les signaux de la vue
        self.view.send_requested.connect(self.on_send_message)
        self.view.copy_requested.connect(self.on_copy_response)
        self.view.new_conversation_requested.connect(self.on_new_conversation)
    
    def on_send_message(self, mode: str, message: str):
        """Gère la demande d'envoi de message (mis à jour pour la nouvelle API assistant)"""
        # Pour le nouvel assistant : ignorer le mode, utiliser le message direct
        # Ajouter le message utilisateur à l'UI immédiatement
        self.view.add_user_message(message)
        self.view.clear_status()
        
        # Afficher chargement
        self.view.set_loading(True)
        
        # Appeler la nouvelle API assistant
        self.api_client.query_assistant_async(
            message=message,
            on_success=self._on_assistant_response,
            on_error=self.on_error
        )
    
    def _on_assistant_response(self, response):
        """Gère la réponse de l'assistant avec support de navigation"""
        self.view.set_loading(False)
        
        # Extraire les données de réponse
        action = response.get("action", "chat_only")
        target_view = response.get("target_view")
        prefill_data = response.get("prefill_data", {})
        response_text = response.get("response_text", "")
        
        # Ajouter la réponse IA à la conversation
        self.view.add_ai_message(response_text, "assistant")
        self.last_response = response_text
        
        # Gérer les actions de navigation
        if action == "navigate":
            if target_view == "flights":
                self.navigate_to_flights.emit(prefill_data)
            elif target_view == "hotels":
                self.navigate_to_hotels.emit(prefill_data)
            elif target_view == "packages":
                self.navigate_to_packages.emit(prefill_data)
            elif target_view == "history":
                self.navigate_to_history.emit(prefill_data)
    
    def on_success(self, response):
        """Gère la réponse LLM réussie"""
        self.view.set_loading(False)
        
        # Vérifier si mode mock
        meta = response.get("meta", {})
        if meta.get("mock", False):
            reason = meta.get("reason", "service_unavailable")
            self.view.show_demo_banner(reason)
        else:
            self.view.hide_demo_banner()
        
        # Ajouter la réponse IA à la conversation
        answer = response.get("answer", "Pas de réponse")
        model = response.get("model", "unknown")
        self.view.add_ai_message(answer, model)
        
        # Stocker pour la fonction copier
        self.last_response = answer
    
    def on_error(self, error):
        """Gère l'erreur API"""
        self.view.set_loading(False)
        self.view.show_error(f"Erreur: {str(error)}")
    
    def on_copy_response(self):
        """Copier la dernière réponse IA dans le presse-papiers"""
        if self.last_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response)
            self.view.show_success("Réponse copiée!")
    
    def on_new_conversation(self):
        """Effacer la conversation et réinitialiser"""
        self.view.clear_conversation()
        self.last_response = ""
        self.view.show_success("Nouvelle conversation démarrée")
    
    def _build_context(self) -> dict:
        """
        Construit le dictionnaire de contexte avec les bons DTOs.
        Récupère le contexte mis en cache depuis la session/navigation si disponible.
        
        Retourne une structure ConsultContext valide.
        """
        # Pour l'instant, retourne un ConsultContext vide mais valide
        # Cela sera rempli lors de la navigation depuis SearchView avec des offres
        return {
            "selected_offers": None,  # Sera une liste de dicts OfferDTO une fois défini
            "booking_info": None,     # Sera un dict BookingDTO une fois défini
            "budget_max": None,       # Sera un int une fois défini
            "user_prefs": {}          # Toujours un dict
        }
    
    def set_initial_context(self, mode: str, context: dict):
        """
        Définit le contexte initial lors de la navigation depuis une autre vue.
        
        Args:
            mode: Mode pré-sélectionné (compare, budget, policy, free)
            context: Contexte pré-rempli (offres, réservation, etc.)
        """
        # Mapper le mode à l'index du sélecteur
        mode_index_map = {
            "compare": 0,
            "budget": 1,
            "policy": 2,
            "free": 3
        }
        
        if mode in mode_index_map:
            self.view.set_mode(mode_index_map[mode])
        
        # Stocker le contexte pour le prochain appel API
        # Ceci serait utilisé par _build_context()
        # TODO: Stocker dans une variable d'instance ou session
