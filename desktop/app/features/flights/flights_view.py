from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QDateEdit, QScrollArea, QGridLayout, QComboBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon
from pathlib import Path
from features.shared.city_autocomplete import CityAutocompleteLineEdit


class FlightCard(QFrame):
    """Widget carte moderne pour afficher une offre de vol."""
    
    book_clicked = Signal(dict)  # Émet les données du vol au clic sur réserver
    
    def __init__(self, flight: dict):
        super().__init__()
        self.flight = flight
        self.setObjectName("flightCard")
        
        # Card styling
        self.setStyleSheet("""
            QFrame#flightCard {
                background: rgba(220, 224, 228, 0.7);
                border: 1px solid rgba(100, 100, 100, 0.15);
                border-radius: 20px;
                padding: 0px;
            }
            QFrame#flightCard:hover {
                background: rgba(230, 234, 238, 0.9);
                border: 1px solid rgba(0, 153, 255, 0.4);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header: Flight badge + Airline
        header = QHBoxLayout()
        flight_badge = QLabel("✈️ VOL")
        flight_badge.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0077b6, stop:1 #0096c7);
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
        """)
        header.addWidget(flight_badge)
        
        airline = flight.get("airline", "Airline")
        airline_label = QLabel(airline)
        airline_label.setStyleSheet("""
            color: #57606a;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        """)
        header.addWidget(airline_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Route (large, prominent)
        departure = flight.get("departure", "")
        destination = flight.get("destination", "")
        route_label = QLabel(f"{departure} → {destination}")
        route_label.setStyleSheet("""
            color: #0077b6;
            font-size: 24px;
            font-weight: 800;
            background: transparent;
        """)
        layout.addWidget(route_label)
        
        # Dates
        depart_date = flight.get("depart_date", "")
        return_date = flight.get("return_date", "")
        dates_label = QLabel(f"📅 {depart_date} - {return_date}")
        dates_label.setStyleSheet("""
            color: #24292f;
            font-size: 15px;
            font-weight: 600;
            background: transparent;
        """)
        layout.addWidget(dates_label)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background: rgba(0, 119, 182, 0.2); max-height: 1px;")
        layout.addWidget(divider)
        
        # Details grid
        details = QGridLayout()
        details.setSpacing(12)
        details.setContentsMargins(0, 8, 0, 8)
        
        duration_min = flight.get("duration_min", 0)
        duration_hours = duration_min // 60
        duration_mins = duration_min % 60
        self._add_detail_row(details, 0, "⏱️ Durée", f"{duration_hours}h {duration_mins}min")
        
        stops = flight.get("stops", 0)
        stops_text = "Direct" if stops == 0 else f"{stops} escale(s)"
        self._add_detail_row(details, 1, "🛫 Escales", stops_text)
        
        score = flight.get("score", 0)
        self._add_detail_row(details, 2, "⭐ Score", f"{score:.1f}/10")
        
        layout.addLayout(details)
        
        # Price section
        price_section = QHBoxLayout()
        
        price = flight.get("price", 0)
        price_label = QLabel(f"{price:.2f} €")
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
        book_btn.clicked.connect(lambda: self.book_clicked.emit(self.flight))
        price_section.addWidget(book_btn)
        
        layout.addLayout(price_section)
    
    def _add_detail_row(self, grid: QGridLayout, row: int, label: str, value: str):
        """Ajoute une ligne de détail à la grille."""
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


class FlightsView(QWidget):
    """
    Vue Vols Moderne - Affiche la recherche de vols et les résultats
    """
    # Signaux pour la navigation
    packages_requested = Signal()
    hotels_requested = Signal()
    history_requested = Signal()
    assistant_requested = Signal()
    
    def __init__(self, api_client=None):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("JetSetGo - Vols")
        
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
        
        # Connect navigation
        self.packages_btn.clicked.connect(self.packages_requested.emit)
        self.hotels_btn.clicked.connect(self.hotels_requested.emit)
        self.history_btn.clicked.connect(self.history_requested.emit)
        self.ai_btn.clicked.connect(self.assistant_requested.emit)
        
        main_layout.addLayout(header)

        # SEARCH PANEL
        search_frame = QFrame()
        search_frame.setObjectName("searchPanel")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(24, 24, 24, 24)
        search_layout.setSpacing(20)

        search_title = QLabel("✈️ Rechercher un Vol")
        search_title.setStyleSheet("""
            color: #0077b6; 
            font-size: 22px; 
            font-weight: 700;
            background: transparent;
        """)
        search_layout.addWidget(search_title)

        # Form grid
        form_grid = QGridLayout()
        form_grid.setSpacing(16)
        
        # Row 1: Departure & Destination
        dep_label = QLabel("Départ")
        dep_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(dep_label, 0, 0)
        
        if self.api:
            self.departure = CityAutocompleteLineEdit(self.api)
            self.departure.setPlaceholderText("Paris, London, NYC...")
        else:
            self.departure = QLineEdit()
            self.departure.setPlaceholderText("Ville de départ")
        self.departure.setMinimumHeight(50)
        form_grid.addWidget(self.departure, 1, 0)
        
        dest_label = QLabel("Destination")
        dest_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(dest_label, 0, 1)
        
        if self.api:
            self.destination = CityAutocompleteLineEdit(self.api)
            self.destination.setPlaceholderText("Tokyo, Dubai, Barcelona...")
        else:
            self.destination = QLineEdit()
            self.destination.setPlaceholderText("Destination")
        self.destination.setMinimumHeight(50)
        form_grid.addWidget(self.destination, 1, 1)
        
        # Row 2: Dates
        depart_label = QLabel("Date de départ")
        depart_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(depart_label, 2, 0)
        
        self.depart_date = QDateEdit()
        self.depart_date.setCalendarPopup(True)
        self.depart_date.setDate(QDate.currentDate().addDays(7))
        self.depart_date.setDisplayFormat("yyyy-MM-dd")
        self.depart_date.setMinimumHeight(50)
        form_grid.addWidget(self.depart_date, 3, 0)
        
        return_label = QLabel("Date de retour")
        return_label.setStyleSheet("color: #57606a; font-weight: 600; font-size: 13px; background: transparent;")
        form_grid.addWidget(return_label, 2, 1)
        
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDate(QDate.currentDate().addDays(14))
        self.return_date.setDisplayFormat("yyyy-MM-dd")
        self.return_date.setMinimumHeight(50)
        form_grid.addWidget(self.return_date, 3, 1)
        
        search_layout.addLayout(form_grid)
        
        # Search button
        self.search_btn = QPushButton("🔍 Rechercher des Vols")
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
            color: #0077b6;
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
        """Définit le message de statut."""
        self.status.setText(text)

    def show_error(self, message: str):
        """Affiche une boîte de dialogue d'erreur."""
        QMessageBox.critical(self, "Erreur", message)
    
    def show_success(self, message: str):
        """Affiche une boîte de dialogue de succès."""
        QMessageBox.information(self, "Succès", message)

    def clear_results(self):
        """Efface toutes les cartes de vols."""
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def display_flights(self, flights: list):
        """Affiche les résultats de vols sous forme de cartes."""
        self.clear_results()
        
        if flights:
            grid = QGridLayout()
            grid.setSpacing(20)
            
            for idx, flight in enumerate(flights):
                card = FlightCard(flight)
                if hasattr(self, '_book_handler'):
                    card.book_clicked.connect(self._book_handler)
                
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)
            
            self.cards_layout.insertLayout(0, grid)
            self.set_status(f"✨ {len(flights)} vol(s) trouvé(s)")
        else:
            empty_label = QLabel("Aucun vol trouvé pour ces critères")
            empty_label.setStyleSheet("""
                color: #57606a;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 60px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, empty_label)
            self.set_status("0 vol trouvé")
    
    def set_book_handler(self, handler):
        """Définit le gestionnaire pour les clics sur le bouton réserver."""
        self._book_handler = handler
    
    # Legacy methods for backward compatibility
    def set_offers(self, offers: list):
        """Méthode héritée - redirige vers display_flights."""
        self.display_flights(offers)
