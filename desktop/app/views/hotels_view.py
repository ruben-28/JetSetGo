from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QIcon
from pathlib import Path
from views.city_autocomplete import CityAutocompleteLineEdit


class HotelsView(QWidget):
    """
    Hotels View - Shows hotel-only search and results
    """
    # Signals for navigation
    packages_requested = Signal()
    flights_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client  # Store API client for autocomplete
        self.setWindowTitle("JetSetGo - Hôtels")
        
        # Try to set window icon
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
        logo_title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        logo_title.setObjectName("appTitle")
        logo_title.setTextFormat(Qt.RichText)
        header.addWidget(logo_title)
        
        header.addStretch()
        
        # Navigation buttons
        self.packages_btn = QPushButton("Packages")
        self.packages_btn.setObjectName("iconButton")
        self.packages_btn.setMinimumHeight(40)
        self.packages_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.packages_btn)
        
        self.flights_btn = QPushButton("Vols")
        self.flights_btn.setObjectName("iconButton")
        self.flights_btn.setMinimumHeight(40)
        self.flights_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.flights_btn)
        
        self.history_btn = QPushButton("Mes Voyages")
        self.history_btn.setObjectName("iconButton")
        self.history_btn.setMinimumHeight(40)
        self.history_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.history_btn)
        
        self.ai_btn = QPushButton("Assistant IA")
        self.ai_btn.setObjectName("iconButton")
        self.ai_btn.setMinimumHeight(40)
        self.ai_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.ai_btn)
        
        profile_btn = QPushButton("Profil")
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
        search_title = QLabel("Rechercher un Hôtel")
        search_title.setObjectName("sectionTitle")
        search_layout.addWidget(search_title)

        # Form fields
        form_row = QHBoxLayout()
        form_row.setSpacing(12)
        
        # Destination/City with Autocomplete
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Ville / Destination (ex: Paris, LON, NYC)")
        else:
            # Fallback to regular LineEdit if no API client
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Ville / Destination")
        self.destination.setMinimumHeight(48)
        form_row.addWidget(self.destination)
        
        # Check-in date
        checkin_label = QLabel("Arrivée:")
        checkin_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(checkin_label)
        
        self.checkin_date = QDateEdit()
        self.checkin_date.setCalendarPopup(True)
        self.checkin_date.setDate(QDate.currentDate().addDays(7))
        self.checkin_date.setDisplayFormat("yyyy-MM-dd")
        self.checkin_date.setMinimumHeight(48)
        self.checkin_date.setMinimumWidth(130)
        form_row.addWidget(self.checkin_date)
        
        # Check-out date
        checkout_label = QLabel("Départ:")
        checkout_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(checkout_label)
        
        self.checkout_date = QDateEdit()
        self.checkout_date.setCalendarPopup(True)
        self.checkout_date.setDate(QDate.currentDate().addDays(14))
        self.checkout_date.setDisplayFormat("yyyy-MM-dd")
        self.checkout_date.setMinimumHeight(48)
        self.checkout_date.setMinimumWidth(130)
        form_row.addWidget(self.checkout_date)
        
        # Guests
        self.guests = QComboBox()
        self.guests.addItems(["1 Pers.", "2 Pers.", "3 Pers.", "4 Pers.", "5+ Pers."])
        self.guests.setMinimumHeight(48)
        form_row.addWidget(self.guests)
        
        search_layout.addLayout(form_row)

        # Search button
        self.search_btn = QPushButton("RECHERCHER DES HÔTELS")
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
        results_label = QLabel("Hôtels Disponibles")
        results_label.setObjectName("sectionTitle")
        results_label.setStyleSheet("color: #0077b6; font-size: 18px; font-weight: 700;")
        main_layout.addWidget(results_label)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom Hôtel", "Prix (€)", "Étoiles", "Localisation", "Score"
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
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(200)
        self.table.setMaximumHeight(400)
        
        # Disable gridlines and focus
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        main_layout.addWidget(self.table)

        # ============================================
        # ACTION BUTTONS
        # ============================================
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsPanel")
        actions_frame.setStyleSheet("""
            QFrame#actionsPanel {
                background: rgba(200, 205, 211, 0.5);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        actions_frame.setFixedHeight(75)
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(15, 10, 15, 10)
        actions_layout.setSpacing(15)
        
        self.details_btn = QPushButton("Voir détails")
        self.details_btn.setObjectName("secondary")
        self.details_btn.setEnabled(False)
        self.details_btn.setMinimumHeight(52)
        self.details_btn.setMinimumWidth(180)
        self.details_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(self.details_btn)

        self.book_btn = QPushButton("RÉSERVER CET HÔTEL")
        self.book_btn.setEnabled(False)
        self.book_btn.setMinimumHeight(52)
        self.book_btn.setMinimumWidth(220)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(self.book_btn)

        actions_layout.addStretch()
        main_layout.addWidget(actions_frame)

        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Connect navigation
        self.packages_btn.clicked.connect(self.packages_requested.emit)
        self.flights_btn.clicked.connect(self.flights_requested.emit)
        self.history_btn.clicked.connect(self.history_requested.emit)
        self.ai_btn.clicked.connect(self.assistant_requested.emit)

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

    def set_hotels(self, hotels: list):
        """Display hotel results in the table"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for hotel in hotels:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            def create_item(text):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor("#24292f"))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                font = item.font()
                font.setStrikeOut(False)
                item.setFont(font)
                return item
            
            self.table.setItem(row, 0, create_item(hotel.get("id", "")))
            self.table.setItem(row, 1, create_item(hotel.get("name", "")))
            self.table.setItem(row, 2, create_item(f"{hotel.get('price', 0)} €"))
            self.table.setItem(row, 3, create_item(f"{hotel.get('stars', 3)} ⭐"))
            self.table.setItem(row, 4, create_item(hotel.get("location", "")))
            self.table.setItem(row, 5, create_item(hotel.get("score", 0.0)))

        self.table.setSortingEnabled(True)
        self.set_status(f"{len(hotels)} hôtel(s) trouvé(s)")

    def get_selected_hotel_data(self):
        """Get data from the currently selected hotel row."""
        selection_model = self.table.selectionModel()
        current_index = selection_model.currentIndex()
        row = current_index.row()
        
        if row < 0:
            return None
        
        id_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        price_item = self.table.item(row, 2)
        
        if not id_item:
            return None
        
        return {
            "id": id_item.text(),
            "name": name_item.text() if name_item else "",
            "price": price_item.text() if price_item else "0"
        }
