from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo")
        self.resize(1400, 900)
        
        # Central widget is a stack to hold different views
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Load stylesheet
        self._load_stylesheet()

    def _load_stylesheet(self):
        """Load the premium theme stylesheet."""
        # Adjust path to find styles directory relative to this file
        # views/main_window.py -> ../styles/premium_theme.qss
        style_path = Path(__file__).parent.parent / "styles" / "premium_theme.qss"
        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def switch_view(self, widget: QWidget):
        """Switch to a new view, adding it to the stack."""
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)
