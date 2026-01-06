import sys
from PySide6.QtWidgets import QApplication

from services.api_client import ApiClient
from views.login_view import LoginView
from presenters.login_presenter import LoginPresenter

def main():
    app = QApplication(sys.argv)

    api = ApiClient(base_url="http://127.0.0.1:8000")
    login_view = LoginView()
    LoginPresenter(login_view, api)

    login_view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
