from services.session import SESSION
from views.search_view import SearchView
from presenters.search_presenter import SearchPresenter
from PySide6.QtWidgets import QApplication
import traceback


class LoginPresenter:
    def __init__(self, view, api_client):
        self.view = view
        self.api = api_client

        self.view.login_btn.clicked.connect(self.on_login)
        self.view.reg_btn.clicked.connect(self.on_register)

    def on_login(self):
        """Handle login button click - now async"""
        print("CLICK LOGIN")
        u = self.view.login_user.text().strip()
        p = self.view.login_pass.text()

        if not u or not p:
            self.view.show_error("Remplis username/email et mot de passe.")
            return

        self._set_loading(True)

        # Call async API (won't freeze UI!)
        self.api.login_async(
            u, p,
            on_success=self._on_login_success,
            on_error=self._on_login_error
        )

    def _on_login_success(self, data):
        """Callback when login succeeds"""
        print("LOGIN RESPONSE:", data)
        
        # Store token and set it in API client
        token = data["access_token"]
        SESSION.set_auth(token, None, None)
        self.api.set_token(token)  # ✅ Now sends token in future requests!
        
        self.view.show_info("Connecté ✅")

        # Open search view
        self.search_view = SearchView()
        self.search_presenter = SearchPresenter(self.search_view, self.api)
        self.search_view.show()
        self.view.close()
        
        self._set_loading(False)

    def _on_login_error(self, error):
        """Callback when login fails"""
        print("LOGIN ERROR:", repr(error))
        traceback.print_exc()
        self.view.show_error(str(error))
        self._set_loading(False)

    def on_register(self):
        """Handle register button click - now async"""
        print("CLICK SIGNUP")
        username = self.view.reg_username.text().strip()
        email = self.view.reg_email.text().strip()
        password = self.view.reg_pass.text()

        if not username or not email or not password:
            self.view.show_error("Remplis username, email et mot de passe.")
            return

        self._set_loading(True)

        # Call async API
        self.api.register_async(
            username, email, password,
            on_success=self._on_register_success,
            on_error=self._on_register_error
        )

    def _on_register_success(self, data):
        """Callback when register succeeds"""
        print("REGISTER RESPONSE:", data)
        
        # Store token and set it in API client
        token = data["access_token"]
        SESSION.set_auth(token, None, None)
        self.api.set_token(token)  # ✅ Now sends token in future requests!
        
        self.view.show_info("Compte créé ✅")
        self.view.tabs.setCurrentIndex(0)
        self._set_loading(False)

    def _on_register_error(self, error):
        """Callback when register fails"""
        print("REGISTER ERROR:", repr(error))
        traceback.print_exc()
        self.view.show_error(str(error))
        self._set_loading(False)

    def _set_loading(self, loading: bool):
        """Update UI loading state"""
        self.view.login_btn.setDisabled(loading)
        self.view.reg_btn.setDisabled(loading)
        self.view.login_btn.setText("⏳ Connexion..." if loading else "Se connecter")
        self.view.reg_btn.setText("⏳ Création..." if loading else "Créer un compte")

