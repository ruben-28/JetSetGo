import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from services.api_client import ApiClient
from views.login_view import LoginView
from presenters.login_presenter import LoginPresenter


def load_stylesheet():
    """Load the light theme stylesheet."""
    style_path = Path(__file__).parent / "styles" / "light_theme.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def main():
    app = QApplication(sys.argv)
    
    # Apply dark theme
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    api = ApiClient(base_url="http://127.0.0.1:8000")
    login_view = LoginView()
    LoginPresenter(login_view, api)

    login_view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

