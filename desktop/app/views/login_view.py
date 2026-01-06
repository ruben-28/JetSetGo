from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTabWidget,
)


class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Connexion")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)

        title = QLabel("JetSetGo")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        root.addWidget(title)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # --- Login tab
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username ou Email")

        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("Mot de passe")
        self.login_pass.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Se connecter")

        login_layout.addWidget(QLabel("Connexion"))
        login_layout.addWidget(self.login_user)
        login_layout.addWidget(self.login_pass)
        login_layout.addWidget(self.login_btn)

        # --- Register tab
        reg_tab = QWidget()
        reg_layout = QVBoxLayout(reg_tab)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Username")

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email")

        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Mot de passe")
        self.reg_pass.setEchoMode(QLineEdit.Password)

        self.reg_btn = QPushButton("Créer un compte")

        reg_layout.addWidget(QLabel("Inscription"))
        reg_layout.addWidget(self.reg_username)
        reg_layout.addWidget(self.reg_email)
        reg_layout.addWidget(self.reg_pass)
        reg_layout.addWidget(self.reg_btn)

        self.tabs.addTab(login_tab, "Login")
        self.tabs.addTab(reg_tab, "Register")

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def show_info(self, message: str):
        QMessageBox.information(self, "Info", message)
