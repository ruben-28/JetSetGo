from views.main_window import MainWindow
from views.login_view import LoginView
from views.search_view import SearchView
from views.history_view import HistoryView
from views.assistant_view import AssistantView
from presenters.login_presenter import LoginPresenter
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
        
        # Search
        self.search_view = SearchView()
        self.search_presenter = SearchPresenter(self.search_view, self.api_client)
        self.search_view.history_btn.clicked.connect(lambda: self.main_window.switch_to_view("history"))
        # Add AI button if it exists
        if hasattr(self.search_view, 'ai_btn'):
            self.search_view.ai_btn.clicked.connect(lambda: self.main_window.switch_to_view("assistant"))
        self.main_window.add_view("search", self.search_view)
        
        # History
        self.history_view = HistoryView()
        self.history_presenter = HistoryPresenter(self.history_view, self.api_client)
        self.history_presenter.back_to_search.connect(lambda: self.main_window.switch_to_view("search"))
        self.main_window.add_view("history", self.history_view)
        
        # Assistant
        self.assistant_view = AssistantView()
        self.assistant_presenter = AssistantPresenter(self.assistant_view, self.api_client)
        self.assistant_view.back_requested.connect(lambda: self.main_window.switch_to_view("search"))
        self.main_window.add_view("assistant", self.assistant_view)
    
    def start(self):
        """Start application"""
        self.main_window.switch_to_view("login")
        self.main_window.showMaximized()
    
    def _on_login_successful(self, user_data):
        """Handle successful login -> Switch to Search"""
        self.main_window.switch_to_view("search")
    
    def cleanup(self):
        """Cleanup resources on app shutdown"""
        # Close HTTP client properly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.api_client.close())
        loop.close()
