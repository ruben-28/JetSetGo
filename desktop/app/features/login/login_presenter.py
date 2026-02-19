from services.session import SESSION
# Decoupled: No more SearchView/SearchPresenter imports
from PySide6.QtWidgets import QApplication
import traceback
from PySide6.QtCore import QObject, Signal


class LoginPresenter(QObject):
    # Signal émis lorsque la connexion réussit, passant le dictionnaire de données utilisateur
    login_successful = Signal(dict)

    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client

        self.view.login_btn.clicked.connect(self.on_login)
        self.view.reg_btn.clicked.connect(self.on_register)

    def on_login(self):
        """Gère le clic sur le bouton de connexion - maintenant asynchrone"""
        print("CLIC CONNEXION")
        u = self.view.login_user.text().strip()
        p = self.view.login_pass.text()

        if not u or not p:
            self.view.show_error("Remplis username/email et mot de passe.")
            return

        self._set_loading(True)

        # Appel API asynchrone (ne gèle pas l'UI !)
        self.api.login_async(
            u, p,
            on_success=self._on_login_success,
            on_error=self._on_login_error
        )

    def _on_login_success(self, data):
        """Callback en cas de succès de connexion"""
        print("RÉPONSE CONNEXION:", data)
        
        # Stocker le token et le définir dans le client API
        token = data["access_token"]
        
        # Décoder le JWT pour obtenir le user_id du claim 'sub'
        user_id = self._decode_user_id_from_token(token)
        username = self.view.login_user.text().strip()
        
        SESSION.set_auth(token, user_id, username)
        self.api.set_token(token)
        
        self.view.show_info("Connecté ✅")
        
        # Émettre le signal au lieu d'ouvrir manuellement de nouvelles fenêtres
        self.login_successful.emit(data)
        
        self._set_loading(False)

    def _decode_user_id_from_token(self, token: str) -> int:
        """Décode le user_id depuis le claim 'sub' du token JWT."""
        import base64
        import json
        try:
            # Format JWT : header.payload.signature
            payload = token.split('.')[1]
            # Ajouter le padding si nécessaire
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return int(data.get('sub', 0))
        except Exception as e:
            print(f"[ATTENTION] Échec du décodage du user_id depuis le token: {e}")
            return None

    def _on_login_error(self, error):
        """Callback en cas d'échec de connexion"""
        print("ERREUR CONNEXION:", repr(error))
        traceback.print_exc()
        self.view.show_error(str(error))
        self._set_loading(False)

    def on_register(self):
        """Gère le clic sur le bouton d'inscription - maintenant asynchrone"""
        print("CLIC INSCRIPTION")
        username = self.view.reg_username.text().strip()
        email = self.view.reg_email.text().strip()
        password = self.view.reg_pass.text()

        if not username or not email or not password:
            self.view.show_error("Remplis username, email et mot de passe.")
            return

        self._set_loading(True)

        # Appel API asynchrone
        self.api.register_async(
            username, email, password,
            on_success=self._on_register_success,
            on_error=self._on_register_error
        )

    def _on_register_success(self, data):
        """Callback en cas de succès d'inscription"""
        print("RÉPONSE INSCRIPTION:", data)
        
        # Stocker le token et le définir dans le client API
        token = data["access_token"]
        
        # Décoder le JWT pour obtenir le user_id du claim 'sub'
        user_id = self._decode_user_id_from_token(token)
        username = self.view.reg_username.text().strip()
        
        SESSION.set_auth(token, user_id, username)
        self.api.set_token(token)
        
        self.view.show_info("Compte créé ✅")
        
        # NOTE: L'inscription implique généralement une connexion, ou demande de se connecter.
        # Pour l'instant, restons sur l'onglet de connexion où nous pourrions auto-connecter.
        # Le code original changeait juste d'onglet.
        self.view.tabs.setCurrentIndex(0)
        self._set_loading(False)

    def _on_register_error(self, error):
        """Callback en cas d'échec d'inscription"""
        print("ERREUR INSCRIPTION:", repr(error))
        traceback.print_exc()
        self.view.show_error(str(error))
        self._set_loading(False)

    def _set_loading(self, loading: bool):
        """Met à jour l'état de chargement de l'UI"""
        self.view.login_btn.setDisabled(loading)
        self.view.reg_btn.setDisabled(loading)
        self.view.login_btn.setText("⏳ Connexion..." if loading else "Se connecter")
        self.view.reg_btn.setText("⏳ Création..." if loading else "Créer un compte")
