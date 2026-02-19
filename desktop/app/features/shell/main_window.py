from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from pathlib import Path


class MainWindow(QMainWindow):
    """
    Fenêtre principale de l'application utilisant QStackedWidget pour la gestion des vues.
    
    Avantages de QStackedWidget :
    - Pas de suppression/ajout manuel de widgets
    - Toutes les vues créées une seule fois au démarrage
    - Navigation rapide (change juste l'index)
    - Pas de fuites de mémoire
    - Pattern standard Qt
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Assistant de Voyage")
        
        # Essayer de définir l'icône de la fenêtre
        # features/shell/main_window.py -> ... -> assets/logo.jpg
        try:
            icon_path = Path(__file__).parent.parent.parent.parent / "assets" / "logo.jpg"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except:
            pass
        
        # Utiliser QStackedWidget pour la gestion des vues
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Suivre les vues par nom pour un accès facile
        self.views = {}  # {"login": LoginView(), "search": SearchView(), ...}
        self.view_callbacks = {}  # {"history": callback_function, ...}
        
        # Charger la feuille de style
        self._load_stylesheet()
    
    def _load_stylesheet(self):
        """Charge la feuille de style du thème premium."""
        # Ajuster le chemin pour trouver le dossier styles relatif à ce fichier
        # features/shell/main_window.py -> .../app/styles/premium_theme.qss
        # features/shell -> features -> app
        style_path = Path(__file__).parent.parent.parent / "styles" / "premium_theme.qss"
        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
    
    def add_view(self, name: str, view: QWidget, on_show_callback=None):
        """
        Ajoute une vue à la pile (appeler une fois par vue).
        
        Args:
            name: Nom unique de la vue (ex: "login", "search", "history", "assistant")
            view: Instance du widget de la vue
            on_show_callback: Callback optionnel à exécuter quand la vue est affichée
        """
        if name not in self.views:
            self.views[name] = view
            self.stacked_widget.addWidget(view)
            if on_show_callback:
                self.view_callbacks[name] = on_show_callback
    
    def switch_to_view(self, name: str):
        """
        Bascule vers la vue par son nom (pas de recréation, pas de fuites mémoire).
        
        Args:
            name: Nom de la vue vers laquelle basculer
        
        Raises:
            ValueError: Si la vue n'est pas enregistrée
        """
        if name in self.views:
            view = self.views[name]
            self.stacked_widget.setCurrentWidget(view)
            
            # Appeler le callback d'activation si enregistré
            if name in self.view_callbacks:
                self.view_callbacks[name]()
        else:
            raise ValueError(f"Vue '{name}' non enregistrée. Appelez add_view() d'abord.")

