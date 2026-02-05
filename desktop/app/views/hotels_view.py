from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QDateEdit, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon
from pathlib import Path
from views.city_autocomplete import CityAutocompleteLineEdit


class HotelCard(QFrame):
    """Modern card widget for displaying a hotel offer."""
    
    book_clicked = Signal(dict)  # Emits hotel data when book button clicked
    
    def __init__(self, hotel: dict):
        super().__init__()
        self.hotel = hotel
        self.setObjectName("hotelCard")
        
        # Card styling
        self.setStyleSheet("""
            QFrame#hotelCard {
                background: rgba(220, 224, 228, 0.7);
                border: 1px solid rgba(100, 100, 100, 0.15);
                border-radius: 20px;
                padding: 0px;
            }
            QFrame#hotelCard:hover {
                background: rgba(230, 234, 238, 0.9);
                border: 1px solid rgba(255, 107, 53, 0.4);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header: Hotel badge + Stars
        header = QHBoxLayout()
        hotel_badge = QLabel("🏨 HÔTEL")
        hotel_badge.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff6b35, stop:1 #ff8c42);
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
        """)
        header.addWidget(hotel_badge)
        
        stars = hotel.get("stars", 3)
        stars_label = QLabel("⭐" * stars)
        stars_label.setStyleSheet("""
            color: #fbbf24;
            font-size: 16px;
            background: transparent;
        """)
        header.addWidget(stars_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Hotel name (large, prominent)
        name = hotel.get("name", "Hotel")
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            color: #ff6b35;
            font-size: 22px;
            font-weight: 800;
            background: transparent;
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Location
        location = hotel.get("location", hotel.get("city", ""))
        location_label = QLabel(f"📍 {location}")
        location_label.setStyleSheet("""
            color: #24292f;
            font-size: 15px;
            font-weight: 600;
            background: transparent;
        """)
        layout.addWidget(location_label)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background: rgba(255, 107, 53, 0.2); max-height: 1px;")
        layout.addWidget(divider)
        
        # Details grid
        details = QGridLayout()
        details.setSpacing(12)
        details.setContentsMargins(0, 8, 0, 8)
        
        rating = hotel.get("rating", 0)
        self._add_detail_row(details, 0, "⭐ Note", f"{rating:.1f}/10")
        
        # Amenities (if available)
        amenities = hotel.get("amenities", [])
        if amenities:
            amenities_text = ", ".join(amenities[:3])  # Show first 3
            self._add_detail_row(details, 1, "✨ Services", amenities_text)
        
        layout.addLayout(details)
        
        # Price section
        price_section = QHBoxLayout()
        
        price = hotel.get("price", 0)
        price_label = QLabel(f"{price:.2f} €")
        price_label.setStyleSheet("""
            color: #ff6b35;
            font-size: 32px;
            font-weight: 800;
            background: transparent;
        """)
        price_section.addWidget(price_label)
        
        per_night = QLabel("/nuit")
        per_night.setStyleSheet("""
            color: #57606a;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            padding-top: 12px;
        """)
        price_section.addWidget(per_night)
        
        price_section.addStretch()
        
        # Book button
        book_btn = QPushButton("Réserver")
        book_btn.setMinimumHeight(48)
        book_btn.setMinimumWidth(140)
        book_btn.setCursor(Qt.PointingHandCursor)
        book_btn.clicked.connect(lambda: self.book_clicked.emit(self.hotel))
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
        value_widget.setWordWrap(True)
        
        grid.addWidget(label_widget, row, 0, Qt.AlignLeft)
        grid.addWidget(value_widget, row, 1, Qt.AlignRight)


class HotelsView(QWidget):
    """
    Modern Hotels View - Shows hotel search and results
    """
    # Signals for navigation
    packages_requested = Signal()
    flights_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("JetSetGo - Hôtels")
        
        icon_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1400, 900)
        self.setObjectName("centralWidget")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # HEADER
        header = QHBoxLayout()
        header.setSpacing(20)
        
        logo_title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        logo_title.setObjectName("appTitle")
        logo_title.setTextFormat(Qt.RichText)
        header.addWidget(logo_title)
        
        header.addStretch()
        
        # Navigation buttons
        self.packages_btn = QPushButton("📦 Packages")
        self.packages_btn.setObjectName("iconButton")
        self.packages_btn.setMinimumHeight(44)
        self.packages_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.packages_btn)
        
        self.flights_btn = QPushButton("✈️ Vols")
        self.flights_btn.setObjectName("iconButton")
        self.flights_btn.setMinimumHeight(44)
        self.flights_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.flights_btn)
        
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
        
        # Connect navigation
        self.packages_btn.clicked.connect(self.packages_requested.emit)
        self.flights_btn.clicked.connect(self.flights_requested.emit)
        self.history_btn.clicked.connect(self.history_requested.emit)
        self.ai_btn.clicked.connect(self.assistant_requested.emit)
        
        main_layout.addLayout(header)

        # SEARCH PANEL
        search_frame = QFrame()
        search_frame.setObjectName("searchPanel")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(24, 24, 24, 24)
        search_layout.setSpacing(20)

        search_title = QLabel("🏨 Rechercher un Hôtel")
        search_title.setStyleSheet("""
            color: #ff6b35; 
            font-size: 22px; 
            font-weight: 700;
            background: transparent;
        """)
        search_layout.addWidget(search_title)

        # Form grid
        form_grid = QGridLayout()
        form_grid.setSpacing(16)
        
        # Row 1: Destination
        dest_label = QLabel("Destination")
        dest_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(dest_label, 0, 0, 1, 2)
        
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Paris, Tokyo, New York...")
        else:
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Ville / Destination")
        self.destination.setMinimumHeight(50)
        form_grid.addWidget(self.destination, 1, 0, 1, 2)
        
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
        
        # Search button
        self.search_btn = QPushButton("🔍 Rechercher des Hôtels")
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

        # STATUS & RESULTS
        self.status = QLabel("")
        self.status.setStyleSheet("""
            color: #ff6b35;
            font-size: 16px;
            font-weight: 600;
            background: transparent;
        """)
        main_layout.addWidget(self.status)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
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
        """Clear all hotel cards."""
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_hotels(self, hotels: list):
        """Display hotel results as cards."""
        self.clear_results()
        
        if hotels:
            grid = QGridLayout()
            grid.setSpacing(20)
            
            for idx, hotel in enumerate(hotels):
                card = HotelCard(hotel)
                if hasattr(self, '_book_handler'):
                    card.book_clicked.connect(self._book_handler)
                
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)
            
            self.cards_layout.insertLayout(0, grid)
            self.set_status(f"✨ {len(hotels)} hôtel(s) trouvé(s)")
        else:
            empty_label = QLabel("Aucun hôtel trouvé pour ces critères")
            empty_label.setStyleSheet("""
                color: #57606a;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 60px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, empty_label)
            self.set_status("0 hôtel trouvé")
    
    def set_book_handler(self, handler):
        """Set the handler for book button clicks."""
        self._book_handler = handler
    
    # Legacy methods for backward compatibility
    def set_hotels(self, hotels: list):
        """Legacy method - redirects to display_hotels."""
        self.display_hotels(hotels)
