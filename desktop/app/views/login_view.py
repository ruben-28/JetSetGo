from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QIcon
from pathlib import Path

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Connexion")
        # Force window icon
        # desktop/app/views/login_view.py -> desktop/assets/logo.jpg
        icon_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1024, 768)  # Grande taille par défaut

        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)  # Centrer le contenu
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # Container pour centrer le form
        container = QWidget()
        container.setFixedWidth(450)  # Garder le formulaire à une largeur raisonnable
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        layout.addWidget(container)

        # Header
        # logo = QLabel("✈")
        # logo.setStyleSheet("font-size: 64px;")
        
        logo = QLabel()
        from PySide6.QtGui import QPixmap
        import os
        # desktop/app/views/login_view.py
        # base (views) -> app -> desktop -> assets
        base_dir = Path(__file__).parent.parent.parent
        logo_path = base_dir / "assets" / "logo.jpg"
        pixmap = QPixmap(str(logo_path))
        
        # Resize nicely (e.g. height 100)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(120, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        else:
            logo.setText("(img not found)")
            logo.setStyleSheet("font-size: 64px;")

        logo.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(logo)

        title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        title.setObjectName("title")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: #24292f;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        subtitle = QLabel("Trouvez les meilleurs vols au meilleur prix")
        subtitle.setObjectName("subtitle")
        subtitle.setStyleSheet("color: #24292f; font-size: 14px; font-weight: 500;")
        subtitle.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(subtitle)

        container_layout.addSpacing(20)

        # Tabs
        self.tabs = QTabWidget()
        container_layout.addWidget(self.tabs)

        # Login Tab
        login_widget = QWidget()
        login_layout = QVBoxLayout(login_widget)
        login_layout.setContentsMargins(20, 20, 20, 20)
        login_layout.setSpacing(15)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username ou Email")
        self.login_user.setMinimumHeight(45)
        self._set_placeholder_color(self.login_user)
        login_layout.addWidget(self.login_user)

        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Mot de passe")
        self.login_pass.setEchoMode(QLineEdit.Password)
        self.login_pass.setMinimumHeight(45)
        self._set_placeholder_color(self.login_pass)
        login_layout.addWidget(self.login_pass)

        self.login_btn = QPushButton("Se connecter")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        login_layout.addWidget(self.login_btn)

        # Connect Enter key to login button
        self.login_user.returnPressed.connect(self.login_btn.click)
        self.login_pass.returnPressed.connect(self.login_btn.click)

        login_layout.addStretch()

        # Register Tab
        register_widget = QWidget()
        register_layout = QVBoxLayout(register_widget)
        register_layout.setContentsMargins(20, 20, 20, 20)
        register_layout.setSpacing(15)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Username")
        self.reg_username.setMinimumHeight(45)
        self._set_placeholder_color(self.reg_username)
        register_layout.addWidget(self.reg_username)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email")
        self.reg_email.setMinimumHeight(45)
        self._set_placeholder_color(self.reg_email)
        register_layout.addWidget(self.reg_email)

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Mot de passe")
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass.setMinimumHeight(45)
        self._set_placeholder_color(self.reg_pass)
        register_layout.addWidget(self.reg_pass)

        self.reg_btn = QPushButton("Créer un compte")
        self.reg_btn.setMinimumHeight(50)
        self.reg_btn.setCursor(Qt.PointingHandCursor)
        register_layout.addWidget(self.reg_btn)

        register_layout.addStretch()

        # Add tabs
        self.tabs.addTab(login_widget, "Connexion")
        self.tabs.addTab(register_widget, "Inscription")

        # Footer
        container_layout.addSpacing(10)
        footer = QLabel("© 2026 JetSetGo")
        footer.setStyleSheet("color: #24292f; font-size: 12px;")
        footer.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(footer)

    def _set_placeholder_color(self, line_edit: QLineEdit):
        """Set placeholder text color."""
        palette = line_edit.palette()
        palette.setColor(QPalette.PlaceholderText, QColor("#6e7781"))
        line_edit.setPalette(palette)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def show_info(self, message: str):
        QMessageBox.information(self, "Info", message)
