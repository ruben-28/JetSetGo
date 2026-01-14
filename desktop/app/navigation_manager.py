from views.main_window import MainWindow
from views.login_view import LoginView
from views.search_view import SearchView
from views.history_view import HistoryView
from presenters.login_presenter import LoginPresenter
from presenters.search_presenter import SearchPresenter
from presenters.history_presenter import HistoryPresenter
from services.async_api_client import AsyncApiClient

class NavigationManager:
    def __init__(self):
        self.api_client = AsyncApiClient(base_url="http://127.0.0.1:8000")
        self.main_window = MainWindow()
        
    def start(self):
        """Start the application flow."""
        self._show_login()
        self.main_window.showMaximized()
        
    def _show_login(self):
        """Load and show the login module."""
        # Instantiate View & Presenter
        self.login_view = LoginView()
        self.login_presenter = LoginPresenter(self.login_view, self.api_client)
        
        # Connect signals
        self.login_presenter.login_successful.connect(self._on_login_successful)
        
        # Switch in Shell
        self.main_window.switch_view(self.login_view)
        
    def _on_login_successful(self, user_data):
        """Handle successful login -> Switch to Search."""
        self._show_search()
        
    def _show_search(self):
        """Load and show the search module."""
        # Instantiate View & Presenter
        self.search_view = SearchView()
        self.search_presenter = SearchPresenter(self.search_view, self.api_client)
        
        # Connect history navigation
        self.search_view.history_btn.clicked.connect(self._show_history)
        
        # Switch in Shell
        self.main_window.switch_view(self.search_view)

    def _show_history(self):
        """Load and show the history module."""
        # Instantiate View & Presenter
        self.history_view = HistoryView()
        self.history_presenter = HistoryPresenter(self.history_view, self.api_client)
        
        # Connect back signal
        self.history_presenter.back_to_search.connect(self._show_search)
        
        # Switch in Shell
        self.main_window.switch_view(self.history_view)

