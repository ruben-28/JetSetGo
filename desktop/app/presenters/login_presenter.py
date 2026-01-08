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
        print("CLICK LOGIN")  # <-- DEBUG
        u = self.view.login_user.text().strip()
        p = self.view.login_pass.text()

        if not u or not p:
            self.view.show_error("Remplis username/email et mot de passe.")
            return

        self._set_loading(True)
        QApplication.processEvents()

        try:
            data = self.api.login(u, p)
            print("LOGIN RESPONSE:", data)

            SESSION.set_auth(data["access_token"], None, None)
            self.view.show_info("Connecté ✅")

            self.search_view = SearchView()
            self.search_presenter = SearchPresenter(self.search_view, self.api)
            self.search_view.show()
            self.view.close()

        except Exception as e:
            print("LOGIN ERROR:", repr(e))
            traceback.print_exc()
            self.view.show_error(str(e))

        finally:
            self._set_loading(False)

    def on_register(self):
        print("CLICK SIGNUP")  # <-- DEBUG
        username = self.view.reg_username.text().strip()
        email = self.view.reg_email.text().strip()
        password = self.view.reg_pass.text()

        if not username or not email or not password:
            self.view.show_error("Remplis username, email et mot de passe.")
            return

        self._set_loading(True)
        QApplication.processEvents()  # <-- IMPORTANT: force l’UI à se mettre à jour

        try:
            data = self.api.register(username, email, password)
            print("REGISTER RESPONSE:", data)  # <-- DEBUG

            SESSION.set_auth(data["access_token"], None, None)
            self.view.show_info("Compte créé ✅")
            self.view.tabs.setCurrentIndex(0)

        except Exception as e:
            print("REGISTER ERROR:", repr(e))
            traceback.print_exc()
            self.view.show_error(str(e))

        finally:
            self._set_loading(False)

    def _set_loading(self, loading: bool):
        self.view.login_btn.setDisabled(loading)
        self.view.reg_btn.setDisabled(loading)
        self.view.login_btn.setText("Connexion..." if loading else "Se connecter")
        self.view.reg_btn.setText("Création..." if loading else "Créer un compte")
