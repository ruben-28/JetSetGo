import sys
from PySide6.QtWidgets import QApplication
from navigation_manager import NavigationManager
from PySide6.QtGui import QIcon
from pathlib import Path

def main():
    app = QApplication(sys.argv)
    
    # Set app icon globally
    app.setWindowIcon(QIcon(str(Path(__file__).parent.parent / "assets" / "logo.jpg")))

    # Launch via NavigationManager
    nav_manager = NavigationManager()
    nav_manager.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
