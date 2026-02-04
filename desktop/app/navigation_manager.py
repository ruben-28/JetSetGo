from views.main_window import MainWindow
from views.login_view import LoginView
from views.packages_view import PackagesView
from views.flights_view import FlightsView
from views.hotels_view import HotelsView
from views.search_view import SearchView
from views.history_view import HistoryView
from views.assistant_view import AssistantView
from presenters.login_presenter import LoginPresenter
from presenters.packages_presenter import PackagesPresenter
from presenters.flights_presenter import FlightsPresenter
from presenters.hotels_presenter import HotelsPresenter
from presenters.search_presenter import SearchPresenter
from presenters.history_presenter import HistoryPresenter
from presenters.assistant_presenter import AssistantPresenter
from services.async_api_client import AsyncApiClient
import asyncio


class NavigationManager:
    """
    Manages navigation between views using QStackedWidget pattern.
    
    All views are created once at startup and cached.
    Navigation is performed via switch_to_view() - no recreation.
    """
    
    def __init__(self):
        self.api_client = AsyncApiClient(base_url="http://127.0.0.1:8000")
        self.main_window = MainWindow()
        
        # Create all views ONCE
        self._create_views()
        
    def _create_views(self):
        """Initialize all views once"""
        # Login
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, self.api_client)
        self.login_presenter.login_successful.connect(self._on_login_successful)
        self.main_window.add_view("login", self.login_view)
        
        # Packages (NEW - default after login)
        self.packages_view = PackagesView()
        self.packages_presenter = PackagesPresenter(self.packages_view, self.api_client)
        # Wire navigation from packages view
        self.packages_view.flights_requested.connect(lambda: self.main_window.switch_to_view("flights"))
        self.packages_view.hotels_requested.connect(lambda: self.main_window.switch_to_view("hotels"))
        self.packages_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.packages_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("packages", self.packages_view)
        
        # Flights (NEW)
        self.flights_view = FlightsView()
        self.flights_presenter = FlightsPresenter(self.flights_view, self.api_client)
        # Wire navigation from flights view
        self.flights_view.packages_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        self.flights_view.hotels_requested.connect(lambda: self.main_window.switch_to_view("hotels"))
        self.flights_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.flights_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("flights", self.flights_view)
        
        # Hotels (NEW)
        self.hotels_view = HotelsView()
        self.hotels_presenter = HotelsPresenter(self.hotels_view, self.api_client)
        # Wire navigation from hotels view
        self.hotels_view.packages_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        self.hotels_view.flights_requested.connect(lambda: self.main_window.switch_to_view("flights"))
        self.hotels_view.history_requested.connect(lambda: self.main_window.switch_to_view("history"))
        self.hotels_view.assistant_requested.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("hotels", self.hotels_view)
        
        # Search (kept for backward compatibility, but packages is now the main view)
        self.search_view = SearchView()
        self.search_presenter = SearchPresenter(self.search_view, self.api_client)
        self.search_view.history_btn.clicked.connect(lambda: self.main_window.switch_to_view("history"))
        if hasattr(self.search_view, 'ai_btn'):
            self.search_view.ai_btn.clicked.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("search", self.search_view)
        
        # History
        self.history_view = HistoryView()
        self.history_presenter = HistoryPresenter(self.history_view, self.api_client)
        self.history_presenter.back_to_search.connect(lambda: self.main_window.switch_to_view("packages"))
        self.main_window.add_view("history", self.history_view)
        
        # Assistant
        self.assistant_view = AssistantView()
        self.assistant_presenter = AssistantPresenter(self.assistant_view, self.api_client)
        self.assistant_view.back_requested.connect(lambda: self.main_window.switch_to_view("packages"))
        self.main_window.add_view("assistant", self.assistant_view)
    
    def start(self):
        """Start application"""
        self.main_window.switch_to_view("login")
        self.main_window.showMaximized()
    
    def _on_login_successful(self, user_data):
        """Handle successful login -> Switch to Packages (home page)"""
        self.main_window.switch_to_view("packages")
    
    def cleanup(self):
        """Cleanup resources on app shutdown"""
        # Close HTTP client properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.api_client.close())
        loop.close()
