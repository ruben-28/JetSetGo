from features.shell.main_window import MainWindow
from features.login.login_view import LoginView
from features.packages.packages_view import PackagesView
from features.flights.flights_view import FlightsView
from features.hotels.hotels_view import HotelsView
from features.search.search_view import SearchView
from features.history.history_view import HistoryView
from features.assistant.assistant_view import AssistantView
from features.login.login_presenter import LoginPresenter
from features.packages.packages_presenter import PackagesPresenter
from features.flights.flights_presenter import FlightsPresenter
from features.hotels.hotels_presenter import HotelsPresenter
from features.search.search_presenter import SearchPresenter
from features.history.history_presenter import HistoryPresenter
from features.assistant.assistant_presenter import AssistantPresenter
from services.async_api_client import AsyncApiClient
import asyncio


class NavigationManager:
    """
    Gère la navigation entre les vues en utilisant le modèle QStackedWidget.
    
    Toutes les vues sont créées une seule fois au démarrage et mises en cache.
    La navigation s'effectue via switch_to_view() - pas de recréation.
    """
    
    def __init__(self):
        self.api_client = AsyncApiClient(base_url="http://127.0.0.1:8000")
        self.main_window = MainWindow()
        
        # Créer toutes les vues UNE SEULE FOIS
        self._create_views()
        
    def _create_views(self):
        """Initialise toutes les vues une seule fois"""
        # Connexion
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, self.api_client)
        self.login_presenter.login_successful.connect(self._on_login_successful)
        self.main_window.add_view("login", self.login_view)
        
        # Packages (NOUVEAU - défaut après connexion)
        self.packages_view = PackagesView(api_client=self.api_client)
        self.packages_presenter = PackagesPresenter(self.packages_view, self.api_client)
        # Câblage de la navigation depuis la vue packages
        self.packages_view.flights_requested.connect(lambda: self.main_window.switch_to_view("flights"))
        self.packages_view.hotels_requested.connect(lambda: self.main_window.switch_to_view("hotels"))
        self.packages_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.packages_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("packages", self.packages_view)
        
        
        # Vols (NOUVEAU)
        self.flights_view = FlightsView(api_client=self.api_client)
        self.flights_presenter = FlightsPresenter(self.flights_view, self.api_client)
        # Câblage de la navigation depuis la vue vols
        self.flights_view.packages_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        self.flights_view.hotels_requested.connect(lambda: self.main_window.switch_to_view("hotels"))
        self.flights_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.flights_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("flights", self.flights_view)
        
        
        # Hôtels (NOUVEAU)
        self.hotels_view = HotelsView(api_client=self.api_client)
        self.hotels_presenter = HotelsPresenter(self.hotels_view, self.api_client)
        # Câblage de la navigation depuis la vue hôtels
        self.hotels_view.packages_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        self.hotels_view.flights_requested.connect(lambda: self.main_window.switch_to_view("flights"))
        self.hotels_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.hotels_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("hotels", self.hotels_view)
        
        # Recherche (conservé pour rétrocompatibilité, mais packages est maintenant la vue principale)
        self.search_view = SearchView()
        self.search_presenter = SearchPresenter(self.search_view, self.api_client)
        self.search_view.history_btn.clicked.connect(lambda: self.main_window.switch_to_view("history"))
        if hasattr(self.search_view, 'ai_btn'):
            self.search_view.ai_btn.clicked.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("search", self.search_view)
        
        # Historique
        self.history_view = HistoryView()
        self.history_presenter = HistoryPresenter(self.history_view, self.api_client)
        self.history_presenter.back_to_search.connect(lambda: self.main_window.switch_to_view("packages"))
        # Ajouter la vue avec callback pour recharger les réservations lors de l'affichage
        self.main_window.add_view("history", self.history_view, 
                                  on_show_callback=self.history_presenter.reload_bookings)
        
        # Assistant
        self.assistant_view = AssistantView()
        self.assistant_presenter = AssistantPresenter(self.assistant_view, self.api_client)
        self.assistant_view.back_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        
        # Connecter les signaux de navigation de l'assistant pour changer de vue avec préremplissage
        self.assistant_presenter.navigate_to_flights.connect(self._navigate_to_flights)
        self.assistant_presenter.navigate_to_hotels.connect(self._navigate_to_hotels)
        self.assistant_presenter.navigate_to_packages.connect(self._navigate_to_packages)
        self.assistant_presenter.navigate_to_history.connect(self._navigate_to_history)
        
        self.main_window.add_view("assistant", self.assistant_view)
    
    def _navigate_to_flights(self, prefill_data: dict):
        """Navigue vers la vue vols avec préremplissage des données"""
        # TODO: Préremplir la destination dans la vue vols
        # Pour l'instant, change juste de vue
        self.main_window.switch_to_view("flights")
    
    def _navigate_to_hotels(self, prefill_data: dict):
        """Navigue vers la vue hôtels avec préremplissage des données"""
        # TODO: Préremplir la destination dans la vue hôtels
        self.main_window.switch_to_view("hotels")
    
    def _navigate_to_packages(self, prefill_data: dict):
        """Navigue vers la vue packages avec préremplissage des données"""
        # TODO: Préremplir la destination dans la vue packages
        self.main_window.switch_to_view("packages")

    def _navigate_to_history(self, prefill_data: dict):
        """Navigue vers la vue historique"""
        self.main_window.switch_to_view("history")
    
    def start(self):
        """Démarre l'application"""
        self.main_window.switch_to_view("login")
        self.main_window.showMaximized()
    
    def _on_login_successful(self, user_data):
        """Gère la connexion réussie -> Bascule vers Packages (page d'accueil)"""
        self.main_window.switch_to_view("packages")
    
    def cleanup(self):
        """Nettoyage des ressources à la fermeture de l'application"""
        # Fermer le client HTTP proprement
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.api_client.close())
        loop.close()
