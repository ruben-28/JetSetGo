from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QDateEdit, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon
from pathlib import Path
from features.shared.city_autocomplete import CityAutocompleteLineEdit


class PackageCard(QFrame):
    """Modern card widget for displaying a package offer."""
    
    book_clicked = Signal(dict)  # Emits package data when book button clicked
    
    def __init__(self, package: dict):
        super().__init__()
        self.package = package
        self.setObjectName("packageCard")
        
        # Card styling with glassmorphism
        self.setStyleSheet("""
            QFrame#packageCard {
                background: rgba(220, 224, 228, 0.7);
                border: 1px solid rgba(100, 100, 100, 0.15);
                border-radius: 20px;
                padding: 0px;
            }
            QFrame#packageCard:hover {
                background: rgba(230, 234, 238, 0.9);
                border: 1px solid rgba(0, 153, 255, 0.4);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header: Package badge
        header = QHBoxLayout()
        package_badge = QLabel("📦 PACKAGE COMPLET")
        package_badge.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #9333ea, stop:1 #a855f7);
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
        """)
        header.addWidget(package_badge)
        header.addStretch()
        layout.addLayout(header)
        
        # Destination (large, prominent)
        flight = package.get("flight", {})
        hotel = package.get("hotel", {})
        
        destination = flight.get("destination", "Destination")
        dest_label = QLabel(f"✈️ {destination}")
        dest_label.setStyleSheet("""
            color: #0077b6;
            font-size: 24px;
            font-weight: 800;
            background: transparent;
        """)
        layout.addWidget(dest_label)
        
        # Hotel name
        hotel_name = hotel.get("name", "Hôtel")
        hotel_label = QLabel(f"🏨 {hotel_name}")
        hotel_label.setStyleSheet("""
            color: #ff6b35;
            font-size: 18px;
            font-weight: 700;
            background: transparent;
        """)
        hotel_label.setWordWrap(True)
        layout.addWidget(hotel_label)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background: rgba(0, 119, 182, 0.2); max-height: 1px;")
        layout.addWidget(divider)
        
        # Details grid
        details = QGridLayout()
        details.setSpacing(12)
        details.setContentsMargins(0, 8, 0, 8)
        
        # Flight details
        departure = flight.get("departure", "")
        depart_date = flight.get("depart_date", "")
        return_date = flight.get("return_date", "")
        airline = flight.get("airline", "")
        
        self._add_detail_row(details, 0, "📍 Départ", f"{departure}")
        self._add_detail_row(details, 1, "📅 Aller", depart_date)
        self._add_detail_row(details, 2, "📅 Retour", return_date)
        if airline:
            self._add_detail_row(details, 3, "✈️ Compagnie", airline)
        
        layout.addLayout(details)
        
        # Price section (prominent)
        price_section = QHBoxLayout()
        
        total_price = package.get("total_price", 0)
        price_label = QLabel(f"{total_price:.2f} €")
        price_label.setStyleSheet("""
            color: #0077b6;
            font-size: 32px;
            font-weight: 800;
            background: transparent;
        """)
        price_section.addWidget(price_label)
        
        price_section.addStretch()
        
        # Book button
        book_btn = QPushButton("Réserver")
        book_btn.setMinimumHeight(48)
        book_btn.setMinimumWidth(140)
        book_btn.setCursor(Qt.PointingHandCursor)
        book_btn.clicked.connect(lambda: self.book_clicked.emit(self.package))
        price_section.addWidget(book_btn)
        
        layout.addLayout(price_section)
    
    def _add_detail_row(self, grid: QGridLayout, row: int, label: str, value: str):
        """Add a detail row to the grid."""
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            color: #57606a;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)
        
        value_widget = QLabel(str(value))
        value_widget.setStyleSheet("""
            color: #24292f;
            font-size: 14px;
            font-weight: 700;
            background: transparent;
        """)
        
        grid.addWidget(label_widget, row, 0, Qt.AlignLeft)
        grid.addWidget(value_widget, row, 1, Qt.AlignRight)


class PackagesView(QWidget):
    """
    Modern Packages View - Shows combined hotel + flight packages
    """
    # Signals for navigation
    flights_requested = Signal()
    hotels_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("JetSetGo - Packages")
        
        # Try to set window icon
        icon_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1400, 900)
        self.setObjectName("centralWidget")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
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
        self.flights_btn = QPushButton("✈️ Vols")
        self.flights_btn.setObjectName("iconButton")
        self.flights_btn.setMinimumHeight(44)
        self.flights_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.flights_btn)
        
        self.hotels_btn = QPushButton("🏨 Hôtels")
        self.hotels_btn.setObjectName("iconButton")
        self.hotels_btn.setMinimumHeight(44)
        self.hotels_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.hotels_btn)
        
        self.history_btn = QPushButton("🎫 Mes Voyages")
        self.history_btn.setObjectName("iconButton")
        self.history_btn.setMinimumHeight(44)
        self.history_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.history_btn)
        
        self.ai_btn = QPushButton("🤖 Assistant IA")
        self.ai_btn.setObjectName("iconButton")
        self.ai_btn.setMinimumHeight(44)
        self.ai_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.ai_btn)
        
        # Connect navigation buttons to signals
        self.flights_btn.clicked.connect(self.flights_requested.emit)
        self.hotels_btn.clicked.connect(self.hotels_requested.emit)
        self.history_btn.clicked.connect(self.history_requested.emit)
        self.ai_btn.clicked.connect(self.assistant_requested.emit)
        
        main_layout.addLayout(header)

        # ============================================
        # SEARCH PANEL (MODERN GLASSMORPHISM)
        # ============================================
        search_frame = QFrame()
        search_frame.setObjectName("searchPanel")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(24, 24, 24, 24)
        search_layout.setSpacing(20)

        # Search title
        search_title = QLabel("🌍 Rechercher un Package Complet")
        search_title.setStyleSheet("""
            color: #0077b6; 
            font-size: 22px; 
            font-weight: 700;
            background: transparent;
        """)
        search_layout.addWidget(search_title)

        # Form grid (2 rows)
        form_grid = QGridLayout()
        form_grid.setSpacing(16)
        
        # Row 1: Origin & Destination
        origin_label = QLabel("Départ")
        origin_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(origin_label, 0, 0)
        
        if self.api:
            self.origin = CityAutocompleteLineEdit(self.api)
            self.origin.setPlaceholderText("Paris, London, NYC...")
        else:
            self.origin = QLineEdit()
            self.origin.setPlaceholderText("Ville de départ")
        self.origin.setMinimumHeight(50)
        form_grid.addWidget(self.origin, 1, 0)
        
        dest_label = QLabel("Destination")
        dest_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(dest_label, 0, 1)
        
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Tokyo, Dubai, Barcelona...")
        else:
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Ville de destination")
        self.destination.setMinimumHeight(50)
        form_grid.addWidget(self.destination, 1, 1)
        
        # Row 2: Dates
        checkin_label = QLabel("Date d'arrivée")
        checkin_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(checkin_label, 2, 0)
        
        self.checkin_date = QDateEdit()
        self.checkin_date.setCalendarPopup(True)
        self.checkin_date.setDate(QDate.currentDate().addDays(7))
        self.checkin_date.setDisplayFormat("yyyy-MM-dd")
        self.checkin_date.setMinimumHeight(50)
        form_grid.addWidget(self.checkin_date, 3, 0)
        
        checkout_label = QLabel("Date de départ")
        checkout_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(checkout_label, 2, 1)
        
        self.checkout_date = QDateEdit()
        self.checkout_date.setCalendarPopup(True)
        self.checkout_date.setDate(QDate.currentDate().addDays(14))
        self.checkout_date.setDisplayFormat("yyyy-MM-dd")
        self.checkout_date.setMinimumHeight(50)
        form_grid.addWidget(self.checkout_date, 3, 1)
        
        search_layout.addLayout(form_grid)
        
        # Search button (full width, prominent)
        self.search_btn = QPushButton("🔍 Rechercher des Packages")
        self.search_btn.setMinimumHeight(56)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 1px;
            }
        """)
        search_layout.addWidget(self.search_btn)
        
        main_layout.addWidget(search_frame)

        # ============================================
        # STATUS & RESULTS SECTION
        # ============================================
        
        # Status label
        self.status = QLabel("")
        self.status.setStyleSheet("""
            color: #0077b6;
            font-size: 16px;
            font-weight: 600;
            background: transparent;
        """)
        main_layout.addWidget(self.status)
        
        # Scroll area for package cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)

    def set_status(self, text: str):
        """Set status message."""
        self.status.setText(text)

    def show_error(self, message: str):
        """Show error dialog."""
        QMessageBox.critical(self, "Erreur", message)
    
    def show_success(self, message: str):
        """Show success dialog."""
        QMessageBox.information(self, "Succès", message)

    def clear_results(self):
        """Clear all package cards."""
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_packages(self, packages: list):
        """Display package results as cards."""
        self.clear_results()
        
        if packages:
            # Create grid for cards (2 columns)
            grid = QGridLayout()
            grid.setSpacing(20)
            
            for idx, package in enumerate(packages):
                card = PackageCard(package)
                # Connect book signal to presenter
                if hasattr(self, '_book_handler'):
                    card.book_clicked.connect(self._book_handler)
                
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)
            
            self.cards_layout.insertLayout(0, grid)
            self.set_status(f"✨ {len(packages)} package(s) trouvé(s)")
        else:
            # Empty state
            empty_label = QLabel("Aucun package trouvé pour ces critères")
            empty_label.setStyleSheet("""
                color: #57606a;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 60px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, empty_label)
            self.set_status("0 package trouvé")
    
    def set_book_handler(self, handler):
        """Set the handler for book button clicks."""
        self._book_handler = handler
