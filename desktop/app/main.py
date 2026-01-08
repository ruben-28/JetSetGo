import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from services.api_client import ApiClient
from views.login_view import LoginView
from presenters.login_presenter import LoginPresenter


def load_stylesheet():
    """Load the premium theme stylesheet."""
    style_path = Path(__file__).parent / "styles" / "premium_theme.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


from PySide6.QtGui import QIcon

def main():
    app = QApplication(sys.argv)
    
    # Set app icon
    # desktop/app/main.py -> desktop/assets/logo.jpg
    app.setWindowIcon(QIcon(str(Path(__file__).parent.parent / "assets" / "logo.jpg")))
    
    # Apply premium theme
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    api = ApiClient(base_url="http://127.0.0.1:8000")
    login_view = LoginView()
    presenter = LoginPresenter(login_view, api)

    login_view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

