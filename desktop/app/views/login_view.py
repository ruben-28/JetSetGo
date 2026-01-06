from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor


class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Connexion")
        self.setFixedSize(420, 520)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        logo = QLabel("✈")
        logo.setStyleSheet("font-size: 42px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("JetSetGo")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Trouvez les meilleurs vols au meilleur prix")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Login Tab
        login_widget = QWidget()
        login_layout = QVBoxLayout(login_widget)
        login_layout.setContentsMargins(20, 20, 20, 20)
        login_layout.setSpacing(15)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username ou Email")
        self.login_user.setMinimumHeight(40)
        self._set_placeholder_color(self.login_user)
        login_layout.addWidget(self.login_user)

        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Mot de passe")
        self.login_pass.setEchoMode(QLineEdit.Password)
        self.login_pass.setMinimumHeight(40)
        self._set_placeholder_color(self.login_pass)
        login_layout.addWidget(self.login_pass)

        self.login_btn = QPushButton("Se connecter")
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        login_layout.addWidget(self.login_btn)

        login_layout.addStretch()

        # Register Tab
        register_widget = QWidget()
        register_layout = QVBoxLayout(register_widget)
        register_layout.setContentsMargins(20, 20, 20, 20)
        register_layout.setSpacing(15)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Username")
        self.reg_username.setMinimumHeight(40)
        self._set_placeholder_color(self.reg_username)
        register_layout.addWidget(self.reg_username)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email")
        self.reg_email.setMinimumHeight(40)
        self._set_placeholder_color(self.reg_email)
        register_layout.addWidget(self.reg_email)

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Mot de passe")
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass.setMinimumHeight(40)
        self._set_placeholder_color(self.reg_pass)
        register_layout.addWidget(self.reg_pass)

        self.reg_btn = QPushButton("Créer un compte")
        self.reg_btn.setMinimumHeight(42)
        self.reg_btn.setCursor(Qt.PointingHandCursor)
        register_layout.addWidget(self.reg_btn)

        register_layout.addStretch()

        # Add tabs
        self.tabs.addTab(login_widget, "Connexion")
        self.tabs.addTab(register_widget, "Inscription")

        # Footer
        layout.addSpacing(5)
        footer = QLabel("© 2026 JetSetGo")
        footer.setStyleSheet("color: #6e7681; font-size: 11px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def _set_placeholder_color(self, line_edit: QLineEdit):
        """Set placeholder text color."""
        palette = line_edit.palette()
        palette.setColor(QPalette.PlaceholderText, QColor("#8b949e"))
        line_edit.setPalette(palette)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def show_info(self, message: str):
        QMessageBox.information(self, "Info", message)
