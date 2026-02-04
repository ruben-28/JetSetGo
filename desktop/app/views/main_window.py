from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from pathlib import Path


class MainWindow(QMainWindow):
    """
    Main application window using QStackedWidget for view management.
    
    Benefits of QStackedWidget:
    - No manual widget removal/addition
    - All views created once at startup
    - Fast navigation (just change index)
    - No memory leaks
    - Qt standard pattern
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Assistant de Voyage")
        
        # Try to set window icon
        try:
            self.setWindowIcon(QIcon("assets/logo.png"))
        except:
            pass  # Icon optional
        
        # Use QStackedWidget for view management
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Track views by name for easy access
        self.views = {}  # {"login": LoginView(), "search": SearchView(), ...}
        self.view_callbacks = {}  # {"history": callback_function, ...}
        
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
    
    def add_view(self, name: str, view: QWidget, on_show_callback=None):
        """
        Add a view to the stack (call once per view).
        
        Args:
            name: Unique view name (e.g., "login", "search", "history", "assistant")
            view: View widget instance
            on_show_callback: Optional callback to run when view is shown
        """
        if name not in self.views:
            self.views[name] = view
            self.stacked_widget.addWidget(view)
            if on_show_callback:
                self.view_callbacks[name] = on_show_callback
    
    def switch_to_view(self, name: str):
        """
        Switch to view by name (no recreation, no memory leaks).
        
        Args:
            name: View name to switch to
        
        Raises:
            ValueError: If view not registered
        """
        if name in self.views:
            view = self.views[name]
            self.stacked_widget.setCurrentWidget(view)
            
            # Call activation callback if registered
            if name in self.view_callbacks:
                self.view_callbacks[name]()
        else:
            raise ValueError(f"View '{name}' not registered. Call add_view() first.")

