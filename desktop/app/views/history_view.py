from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from pathlib import Path


class BookingCard(QFrame):
    """Modern card widget for displaying a single booking."""
    
    clicked = Signal(dict)  # Emits booking data when clicked
    
    def __init__(self, booking: dict):
        super().__init__()
        self.booking = booking
        self.setObjectName("bookingCard")
        self.setCursor(Qt.PointingHandCursor)
        
        # Card styling
        self.setStyleSheet("""
            QFrame#bookingCard {
                background: rgba(220, 224, 228, 0.6);
                border: 1px solid rgba(100, 100, 100, 0.1);
                border-radius: 16px;
                padding: 0px;
            }
            QFrame#bookingCard:hover {
                background: rgba(230, 234, 238, 0.8);
                border: 1px solid rgba(0, 153, 255, 0.3);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header row: Type badge + Status badge
        header = QHBoxLayout()
        header.setSpacing(10)
        
        # Type badge
        booking_type = booking.get("booking_type", "FLIGHT")
        type_info = self._get_type_info(booking_type)
        type_badge = QLabel(type_info["label"])
        type_badge.setStyleSheet(f"""
            background: {type_info["color"]};
            color: white;
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
        """)
        header.addWidget(type_badge)
        
        header.addStretch()
        
        # Status badge
        status = booking.get("status", "UNKNOWN")
        status_badge = QLabel(status.upper())
        status_color = "#22c55e" if status == "CONFIRMED" else "#ef4444"
        status_badge.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.9);
            color: {status_color};
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 11px;
            border: 2px solid {status_color};
        """)
        header.addWidget(status_badge)
        
        layout.addLayout(header)
        
        # Destination/Title (large, prominent)
        destination = self._get_destination_text(booking)
        dest_label = QLabel(destination)
        dest_label.setStyleSheet("""
            color: #0077b6;
            font-size: 20px;
            font-weight: 700;
            background: transparent;
        """)
        dest_label.setWordWrap(True)
        layout.addWidget(dest_label)
        
        # Details grid
        details_grid = QGridLayout()
        details_grid.setSpacing(12)
        details_grid.setContentsMargins(0, 8, 0, 0)
        
        row = 0
        
        # Departure (if applicable)
        departure = self._get_departure_text(booking)
        if departure and departure != "—":
            self._add_detail_row(details_grid, row, "📍 Départ", departure)
            row += 1
        
        # Date
        date = self._get_date_text(booking)
        if date:
            self._add_detail_row(details_grid, row, "📅 Date", date)
            row += 1
        
        # Price
        price = booking.get("price", 0)
        self._add_detail_row(details_grid, row, "💰 Prix", f"{price:.2f} €")
        row += 1
        
        # Booking ID (small, subtle)
        booking_id = booking.get("id", "")[:12] + "..."
        id_label = QLabel(f"ID: {booking_id}")
        id_label.setStyleSheet("""
            color: #57606a;
            font-size: 11px;
            background: transparent;
        """)
        details_grid.addWidget(id_label, row, 0, 1, 2)
        
        layout.addLayout(details_grid)
        
    def _get_type_info(self, booking_type: str) -> dict:
        """Get type-specific styling info."""
        types = {
            "FLIGHT": {"label": "✈️ VOL", "color": "#0077b6"},
            "HOTEL": {"label": "🏨 HÔTEL", "color": "#ff6b35"},
            "PACKAGE": {"label": "📦 PACKAGE", "color": "#9333ea"}
        }
        return types.get(booking_type, {"label": booking_type, "color": "#6b7280"})
    
    def _get_destination_text(self, booking: dict) -> str:
        """Get formatted destination text based on booking type."""
        booking_type = booking.get("booking_type", "FLIGHT")
        
        if booking_type == "HOTEL":
            hotel_name = booking.get("hotel_name", "")
            hotel_city = booking.get("hotel_city", "")
            return f"{hotel_name}" if hotel_name else hotel_city
        elif booking_type == "PACKAGE":
            dest = booking.get("destination", "")
            hotel_name = booking.get("hotel_name", "")
            return f"{dest} - {hotel_name}" if hotel_name else dest
        else:  # FLIGHT
            return booking.get("destination", "Destination inconnue")
    
    def _get_departure_text(self, booking: dict) -> str:
        """Get departure text based on booking type."""
        booking_type = booking.get("booking_type", "FLIGHT")
        
        if booking_type == "HOTEL":
            return "—"
        else:
            return booking.get("departure", "")
    
    def _get_date_text(self, booking: dict) -> str:
        """Get date text based on booking type."""
        booking_type = booking.get("booking_type", "FLIGHT")
        
        if booking_type == "HOTEL":
            return booking.get("check_in", "")
        else:
            return booking.get("depart_date", "")
    
    def _add_detail_row(self, grid: QGridLayout, row: int, label: str, value: str):
        """Add a detail row to the grid."""
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            color: #57606a;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)
        
        value_widget = QLabel(value)
        value_widget.setStyleSheet("""
            color: #24292f;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
        """)
        
        grid.addWidget(label_widget, row, 0, Qt.AlignLeft)
        grid.addWidget(value_widget, row, 1, Qt.AlignRight)
    
    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.booking)
        super().mousePressEvent(event)


class HistoryView(QWidget):
    """Modern card-based view for displaying user's booking history."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JetSetGo - Mes Voyages")
        
        # Force window icon
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
        # HEADER
        # ============================================
        header = QHBoxLayout()
        header.setSpacing(20)
        
        # Logo/Title
        logo_title = QLabel('JetSet<span style="color: #ff6b35;">Go</span>')
        logo_title.setObjectName("appTitle")
        logo_title.setTextFormat(Qt.RichText)
        header.addWidget(logo_title)
        
        header.addStretch()
        
        # Back button
        self.back_btn = QPushButton("← Retour à la recherche")
        self.back_btn.setObjectName("secondary")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.back_btn)
        
        main_layout.addLayout(header)

        # ============================================
        # TITLE & STATUS ROW
        # ============================================
        title_row = QHBoxLayout()
        
        title = QLabel("Mes Voyages")
        title.setStyleSheet("color: #0077b6; font-size: 28px; font-weight: 700; background: transparent;")
        title_row.addWidget(title)
        
        title_row.addStretch()
        
        # Status label (count)
        self.status = QLabel("")
        self.status.setStyleSheet("""
            color: #57606a; 
            font-size: 15px; 
            font-weight: 600;
            background: rgba(200, 205, 211, 0.5);
            padding: 8px 16px;
            border-radius: 8px;
        """)
        title_row.addWidget(self.status)
        
        main_layout.addLayout(title_row)

        # ============================================
        # SCROLL AREA WITH CARDS
        # ============================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        # Container for cards
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()  # Push cards to top
        
        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)

    def set_status(self, text: str):
        """Set status message."""
        self.status.setText(text)

    def show_error(self, message: str):
        """Show error dialog."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Erreur", message)

    def set_bookings(self, bookings: list):
        """Populate view with booking cards."""
        # Clear existing cards
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add cards in a grid layout for better space utilization
        if bookings:
            # Create grid for cards (2 columns)
            grid = QGridLayout()
            grid.setSpacing(16)
            
            for idx, booking in enumerate(bookings):
                card = BookingCard(booking)
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)
            
            # Add grid to main layout
            self.cards_layout.insertLayout(0, grid)
            
            self.set_status(f"🎫 {len(bookings)} réservation(s)")
        else:
            # Empty state
            empty_label = QLabel("Aucune réservation trouvée")
            empty_label.setStyleSheet("""
                color: #57606a;
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                padding: 60px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            self.cards_layout.insertWidget(0, empty_label)
            self.set_status("0 réservation")
