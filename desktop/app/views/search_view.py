from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPalette, QColor, QIcon
from pathlib import Path


class SearchView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Recherche de Vols")
        
        # Force window icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1400, 900)
        self.setObjectName("centralWidget")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)

        # ============================================
        # HEADER WITH LOGO & NAVIGATION
        # ============================================
        header = QHBoxLayout()
        header.setSpacing(20)
        
        # Logo/Title
        logo_title = QLabel('✈️ JetSet<span style="color: #ff6b35;">Go</span>')
        logo_title.setObjectName("appTitle")
        logo_title.setTextFormat(Qt.RichText)
        header.addWidget(logo_title)
        
        header.addStretch()
        
        # Navigation buttons
        flights_btn = QPushButton("Flights")
        flights_btn.setObjectName("iconButton")
        flights_btn.setMinimumHeight(40)
        header.addWidget(flights_btn)
        
        hotels_btn = QPushButton("Hotels")
        hotels_btn.setObjectName("iconButton")
        hotels_btn.setMinimumHeight(40)
        header.addWidget(hotels_btn)
        
        profile_btn = QPushButton("Profile")
        profile_btn.setObjectName("iconButton")
        profile_btn.setMinimumHeight(40)
        header.addWidget(profile_btn)
        
        main_layout.addLayout(header)

        # ============================================
        # SEARCH PANEL (GLASSMORPHISM)
        # ============================================
        search_frame = QFrame()
        search_frame.setObjectName("searchPanel")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(20, 20, 20, 20)
        search_layout.setSpacing(18)

        # Search title
        search_title = QLabel("Rechercher votre vol")
        search_title.setObjectName("sectionTitle")
        search_layout.addWidget(search_title)

        # Single row with ALL fields
        form_row = QHBoxLayout()
        form_row.setSpacing(12)
        
        # Departure
        self.departure = QLineEdit()
        self.departure.setPlaceholderText("✈️ Départ")
        self.departure.setMinimumHeight(48)
        form_row.addWidget(self.departure)
        
        # Destination
        self.destination = QLineEdit()
        self.destination.setPlaceholderText("🌍 Destination")
        self.destination.setMinimumHeight(48)
        form_row.addWidget(self.destination)
        
        # Departure date
        self.depart_date = QLineEdit()
        self.depart_date.setPlaceholderText("📅 Départ")
        self.depart_date.setMinimumHeight(48)
        form_row.addWidget(self.depart_date)
        
        # Return date
        self.return_date = QLineEdit()
        self.return_date.setPlaceholderText("📅 Retour")
        self.return_date.setMinimumHeight(48)
        form_row.addWidget(self.return_date)
        
        # Passengers
        self.passengers = QComboBox()
        self.passengers.addItems(["1 Pass.", "2 Pass.", "3 Pass.", "4 Pass.", "5+ Pass."])
        self.passengers.setMinimumHeight(48)
        form_row.addWidget(self.passengers)
        
        # Budget
        self.budget = QLineEdit()
        self.budget.setPlaceholderText("💰 Budget")
        self.budget.setMinimumHeight(48)
        form_row.addWidget(self.budget)
        
        search_layout.addLayout(form_row)

        # Search button
        self.search_btn = QPushButton("🔍 RECHERCHER DES VOLS")
        self.search_btn.setMinimumHeight(52)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        search_layout.addWidget(self.search_btn)

        main_layout.addWidget(search_frame)

        # ============================================
        # STATUS MESSAGE
        # ============================================
        self.status = QLabel("")
        self.status.setStyleSheet("color: #0077b6; font-size: 14px; font-weight: 600;")
        main_layout.addWidget(self.status)

        # ============================================
        # RESULTS TABLE
        # ============================================
        results_label = QLabel("Résultats de recherche")
        results_label.setObjectName("sectionTitle")
        results_label.setStyleSheet("color: #0077b6; font-size: 18px; font-weight: 700;")
        main_layout.addWidget(results_label)

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
        self.table.setMinimumHeight(300)
        main_layout.addWidget(self.table)

        # ============================================
        # ACTION BUTTONS
        # ============================================
        actions = QHBoxLayout()
        actions.setSpacing(15)
        
        self.details_btn = QPushButton("📋 Voir détails")
        self.details_btn.setObjectName("secondary")
        self.details_btn.setEnabled(False)
        self.details_btn.setMinimumHeight(48)
        self.details_btn.setCursor(Qt.PointingHandCursor)
        actions.addWidget(self.details_btn)

        self.book_btn = QPushButton("✅ RÉSERVER CE VOL")
        self.book_btn.setEnabled(False)
        self.book_btn.setMinimumHeight(48)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        actions.addWidget(self.book_btn)

        actions.addStretch()
        main_layout.addLayout(actions)

        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

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
        import json
        with open("debug_offers.log", "w") as f:
            f.write(json.dumps(offers, default=str, indent=2))

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
        
        self.set_status(f"✨ {len(offers)} vol(s) trouvé(s)")
