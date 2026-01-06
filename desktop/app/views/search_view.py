from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor


class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Recherche de Vols")
        self.setMinimumSize(950, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        
        title = QLabel("✈ JetSetGo")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #58a6ff;")
        header.addWidget(title)
        
        header.addStretch()
        
        user_label = QLabel("Utilisateur")
        user_label.setStyleSheet("color: #8b949e;")
        header.addWidget(user_label)
        
        layout.addLayout(header)

        # Search Form
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        self.destination = QLineEdit()
        self.destination.setPlaceholderText("Destination")
        self.destination.setMinimumHeight(36)
        self._set_placeholder_color(self.destination)
        form_layout.addWidget(self.destination)

        self.depart_date = QLineEdit()
        self.depart_date.setPlaceholderText("Départ (YYYY-MM-DD)")
        self.depart_date.setMinimumHeight(36)
        self._set_placeholder_color(self.depart_date)
        form_layout.addWidget(self.depart_date)

        self.return_date = QLineEdit()
        self.return_date.setPlaceholderText("Retour (YYYY-MM-DD)")
        self.return_date.setMinimumHeight(36)
        self._set_placeholder_color(self.return_date)
        form_layout.addWidget(self.return_date)

        self.budget = QLineEdit()
        self.budget.setPlaceholderText("Budget (€)")
        self.budget.setMinimumHeight(36)
        self.budget.setMaximumWidth(150)
        self._set_placeholder_color(self.budget)
        form_layout.addWidget(self.budget)

        self.search_btn = QPushButton("Rechercher")
        self.search_btn.setMinimumHeight(36)
        self.search_btn.setMinimumWidth(120)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        form_layout.addWidget(self.search_btn)

        layout.addLayout(form_layout)

        # Status
        self.status = QLabel("")
        self.status.setStyleSheet("color: #8b949e; font-size: 13px;")
        layout.addWidget(self.status)

        # Results Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Compagnie", "Prix (€)", "Durée (min)", "Escales", "Score"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Actions
        actions = QHBoxLayout()
        
        self.details_btn = QPushButton("Voir détails")
        self.details_btn.setObjectName("secondary")
        self.details_btn.setEnabled(False)
        self.details_btn.setMinimumHeight(38)
        self.details_btn.setCursor(Qt.PointingHandCursor)
        actions.addWidget(self.details_btn)

        self.book_btn = QPushButton("Réserver")
        self.book_btn.setEnabled(False)
        self.book_btn.setMinimumHeight(38)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        actions.addWidget(self.book_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _set_placeholder_color(self, line_edit: QLineEdit):
        """Set placeholder text color."""
        palette = line_edit.palette()
        palette.setColor(QPalette.PlaceholderText, QColor("#8b949e"))
        line_edit.setPalette(palette)

    def _on_selection_changed(self):
        has_selection = len(self.table.selectedItems()) > 0
        self.details_btn.setEnabled(has_selection)
        self.book_btn.setEnabled(has_selection)

    def set_status(self, text: str):
        self.status.setText(text)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def show_info(self, message: str):
        QMessageBox.information(self, "Info", message)

    def set_offers(self, offers: list):
        self.table.setRowCount(0)
        for offer in offers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(offer["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(offer["airline"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(offer["price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(offer["duration_min"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(offer["stops"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(offer["score"])))
        
        self.set_status(f"{len(offers)} vol(s) trouvé(s)")
