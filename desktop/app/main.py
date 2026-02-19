import sys
from PySide6.QtWidgets import QApplication
from navigation_manager import NavigationManager
from PySide6.QtGui import QIcon
from pathlib import Path

def main():
    app = QApplication(sys.argv)
    
    # Définir l'icône de l'application globalement
    app.setWindowIcon(QIcon(str(Path(__file__).parent.parent / "assets" / "logo.jpg")))

    # Créer le gestionnaire de navigation
    nav = NavigationManager()
    
    # Connecter le nettoyage à la fermeture de l'application
    app.aboutToQuit.connect(nav.cleanup)
    
    # Démarrer l'application
    nav.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
