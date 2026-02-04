from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QIcon
from pathlib import Path
from views.city_autocomplete import CityAutocompleteLineEdit


class PackagesView(QWidget):
    """
    Packages View - Shows combined hotel + flight packages (default home page after login)
    """
    # Signals for navigation
    flights_requested = Signal()
    hotels_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client  # Store API client for autocomplete
        self.setWindowTitle("JetSetGo - Packages")
        
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
        self.flights_btn = QPushButton("Vols")
        self.flights_btn.setObjectName("iconButton")
        self.flights_btn.setMinimumHeight(40)
        self.flights_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.flights_btn)
        
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
        search_title = QLabel("Rechercher un Package (Hôtel + Vol)")
        search_title.setObjectName("sectionTitle")
        search_layout.addWidget(search_title)

        # Single row with ALL fields
        form_row = QHBoxLayout()
        form_row.setSpacing(12)
        
        # Destination with Autocomplete
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Destination (ex: Paris, LON, Tokyo)")
        else:
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Destination")
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
        
        # Passengers
        self.passengers = QComboBox()
        self.passengers.addItems(["1 Pers.", "2 Pers.", "3 Pers.", "4 Pers.", "5+ Pers."])
        self.passengers.setMinimumHeight(48)
        form_row.addWidget(self.passengers)
        
        # Budget
        self.budget = QLineEdit()
        self.budget.setPlaceholderText("Budget")
        self.budget.setMinimumHeight(48)
        form_row.addWidget(self.budget)
        
        search_layout.addLayout(form_row)

        # Search button
        self.search_btn = QPushButton("RECHERCHER DES PACKAGES")
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
        results_label = QLabel("Packages Disponibles")
        results_label.setObjectName("sectionTitle")
        results_label.setStyleSheet("color: #0077b6; font-size: 18px; font-weight: 700;")
        main_layout.addWidget(results_label)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom Package", "Prix (€)", "Hôtel", "Vol", "Durée (j)", "Score"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
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

        self.book_btn = QPushButton("RÉSERVER CE PACKAGE")
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
        self.flights_btn.clicked.connect(self.flights_requested.emit)
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

    def set_packages(self, packages: list):
        """Display package results in the table"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for package in packages:
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
            
            self.table.setItem(row, 0, create_item(package.get("id", "")))
            self.table.setItem(row, 1, create_item(package.get("name", "Package Vacances")))
            self.table.setItem(row, 2, create_item(f"{package.get('price', 0)} €"))
            self.table.setItem(row, 3, create_item(package.get("hotel", "Hôtel inclus")))
            self.table.setItem(row, 4, create_item(package.get("flight", "Vol inclus")))
            self.table.setItem(row, 5, create_item(package.get("duration_days", 7)))
            self.table.setItem(row, 6, create_item(package.get("score", 0.0)))

        self.table.setSortingEnabled(True)
        self.set_status(f"{len(packages)} package(s) trouvé(s)")

    def get_selected_package_data(self):
        """Get data from the currently selected package row."""
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
