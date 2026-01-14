from services.session import SESSION
# Decoupled: No more SearchView/SearchPresenter imports
from PySide6.QtWidgets import QApplication
import traceback
from PySide6.QtCore import QObject, Signal


class LoginPresenter(QObject):
    # Signal emitted when login is successful, passing user data dict
    login_successful = Signal(dict)

    def __init__(self, view, api_client):
        super().__init__()
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
        
        # Decode JWT to get user_id from 'sub' claim
        user_id = self._decode_user_id_from_token(token)
        username = self.view.login_user.text().strip()
        
        SESSION.set_auth(token, user_id, username)
        self.api.set_token(token)
        
        self.view.show_info("Connecté ✅")
        
        # Emit signal instead of manually opening new windows
        self.login_successful.emit(data)
        
        self._set_loading(False)

    def _decode_user_id_from_token(self, token: str) -> int:
        """Decode user_id from JWT token's 'sub' claim."""
        import base64
        import json
        try:
            # JWT format: header.payload.signature
            payload = token.split('.')[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return int(data.get('sub', 0))
        except Exception as e:
            print(f"[WARNING] Failed to decode user_id from token: {e}")
            return None

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
        
        # Decode JWT to get user_id from 'sub' claim
        user_id = self._decode_user_id_from_token(token)
        username = self.view.reg_username.text().strip()
        
        SESSION.set_auth(token, user_id, username)
        self.api.set_token(token)
        
        self.view.show_info("Compte créé ✅")
        
        # NOTE: Registration usually implies login, or asks to login. 
        # For now, let's keep it on the login tab or we could auto-login.
        # The original code just switched tabs. We kept that behavior but we could emit success if we wanted auto-login.
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
