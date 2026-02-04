from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QIcon
from pathlib import Path
from views.city_autocomplete import CityAutocompleteLineEdit


class FlightsView(QWidget):
    """
    Flights View - Shows flight-only search and results
    """
    # Signals for navigation
    packages_requested = Signal()
    hotels_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client  # Store API client for autocomplete
        self.setWindowTitle("JetSetGo - Vols")
        
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
        
        self.hotels_btn = QPushButton("Hôtels")
        self.hotels_btn.setObjectName("iconButton")
        self.hotels_btn.setMinimumHeight(40)
        self.hotels_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.hotels_btn)
        
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
        search_title = QLabel("Rechercher un Vol")
        search_title.setObjectName("sectionTitle")
        search_layout.addWidget(search_title)

        # Form fields
        form_row = QHBoxLayout()
        form_row.setSpacing(12)
        
        # Departure city with Autocomplete
        if self.api:
            self.departure = CityAutocompleteLineEdit(self.api)
            self.departure.setPlaceholderText("Ville de départ (ex: Paris, LON)")
        else:
            self.departure = QLineEdit()
            self.departure.setPlaceholderText("Ville de départ")
        self.departure.setMinimumHeight(48)
        form_row.addWidget(self.departure)
        
        # Destination with Autocomplete
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Destination (ex: New York, TYO)")
        else:
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Destination")
        self.destination.setMinimumHeight(48)
        form_row.addWidget(self.destination)
        
        # Departure date
        depart_date_label = QLabel("Départ:")
        depart_date_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(depart_date_label)
        
        self.depart_date = QDateEdit()
        self.depart_date.setCalendarPopup(True)
        self.depart_date.setDate(QDate.currentDate().addDays(7))
        self.depart_date.setDisplayFormat("yyyy-MM-dd")
        self.depart_date.setMinimumHeight(48)
        self.depart_date.setMinimumWidth(130)
        form_row.addWidget(self.depart_date)
        
        # Return date
        return_date_label = QLabel("Retour:")
        return_date_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(return_date_label)
        
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDate(QDate.currentDate().addDays(14))
        self.return_date.setDisplayFormat("yyyy-MM-dd")
        self.return_date.setMinimumHeight(48)
        self.return_date.setMinimumWidth(130)
        form_row.addWidget(self.return_date)
        
        # Passengers
        self.passengers = QComboBox()
        self.passengers.addItems(["1 Pass.", "2 Pass.", "3 Pass.", "4 Pass.", "5+ Pass."])
        self.passengers.setMinimumHeight(48)
        form_row.addWidget(self.passengers)
        
        # Stops filter
        self.stops_filter = QComboBox()
        self.stops_filter.addItems(["Tous les vols", "Direct uniquement", "Maximum 1 escale"])
        self.stops_filter.setMinimumHeight(48)
        self.stops_filter.setToolTip("Filtrer par nombre d'escales")
        form_row.addWidget(self.stops_filter)
        
        search_layout.addLayout(form_row)

        # Search button
        self.search_btn = QPushButton("RECHERCHER DES VOLS")
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
        results_label = QLabel("Vols Disponibles")
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

        self.book_btn = QPushButton("RÉSERVER CE VOL")
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
        self.hotels_btn.clicked.connect(self.hotels_requested.emit)
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

    def set_offers(self, offers: list):
        """Display flight results in the table"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for offer in offers:
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
            
            self.table.setItem(row, 0, create_item(offer.get("id", "")))
            self.table.setItem(row, 1, create_item(offer.get("airline", "")))
            self.table.setItem(row, 2, create_item(f"{offer.get('price', 0)} €"))
            self.table.setItem(row, 3, create_item(f"{offer.get('duration_min', 0)} min"))
            self.table.setItem(row, 4, create_item(offer.get("stops", 0)))
            self.table.setItem(row, 5, create_item(offer.get("score", 0.0)))

        self.table.setSortingEnabled(True)
        self.set_status(f"{len(offers)} vol(s) trouvé(s)")

    def get_selected_flight_data(self):
        """Get data from the currently selected flight row."""
        selection_model = self.table.selectionModel()
        current_index = selection_model.currentIndex()
        row = current_index.row()
        
        if row < 0:
            return None
        
        id_item = self.table.item(row, 0)
        airline_item = self.table.item(row, 1)
        price_item = self.table.item(row, 2)
        
        if not id_item:
            return None
        
        return {
            "id": id_item.text(),
            "airline": airline_item.text() if airline_item else "",
            "price": price_item.text() if price_item else "0"
        }
