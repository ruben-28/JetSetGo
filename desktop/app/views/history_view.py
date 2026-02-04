from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from pathlib import Path


class HistoryView(QWidget):
    """View for displaying user's booking history."""
    
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
        main_layout.setContentsMargins(25, 25, 25, 25)
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

        # TITLE
        # ============================================
        title = QLabel("Mes Voyages")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("color: #0077b6; font-size: 24px; font-weight: 700;")
        main_layout.addWidget(title)

        # ============================================
        # STATUS
        # ============================================
        self.status = QLabel("")
        self.status.setStyleSheet("color: #0077b6; font-size: 14px; font-weight: 600;")
        main_layout.addWidget(self.status)

        # ============================================
        # BOOKINGS TABLE
        # ============================================
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Type", "Départ", "Destination", "Date", "Prix (€)", "Statut"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure column widths
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header_view.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Départ
        header_view.setSectionResizeMode(3, QHeaderView.Stretch)           # Destination
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Date
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Prix
        header_view.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Statut
        
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(400)
        
        # Disable gridlines (consistent with search_view)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        main_layout.addWidget(self.table)
        main_layout.addStretch()

    def set_status(self, text: str):
        """Set status message."""
        self.status.setText(text)

    def show_error(self, message: str):
        """Show error dialog."""
        QMessageBox.critical(self, "Erreur", message)

    def set_bookings(self, bookings: list):
        """Populate table with bookings data."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for booking in bookings:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Helper to create items
            def create_item(text):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor("#24292f"))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                return item
            
            # Get booking type (default to FLIGHT for backward compatibility)
            booking_type = booking.get("booking_type", "FLIGHT")
            
            # Column 0: Short ID (first 8 chars)
            short_id = booking.get("id", "")[:8] + "..."
            self.table.setItem(row, 0, create_item(short_id))
            
            # Column 1: Type in French
            type_labels = {
                "FLIGHT": "✈️ Vol",
                "HOTEL": "🏨 Hôtel", 
                "PACKAGE": "📦 Package"
            }
            type_label = type_labels.get(booking_type, booking_type)
            self.table.setItem(row, 1, create_item(type_label))
            
            # Column 2: Départ (varies by type)
            if booking_type == "HOTEL":
                # Hotels don't have a departure city
                departure = "—"
            elif booking_type == "PACKAGE":
                departure = booking.get("departure", "")
            else:  # FLIGHT
                departure = booking.get("departure", "")
            
            self.table.setItem(row, 2, create_item(departure))
            
            # Column 3: Destination (varies by type)
            if booking_type == "HOTEL":
                # For hotels, show hotel name and city
                hotel_name = booking.get("hotel_name", "")
                hotel_city = booking.get("hotel_city", "")
                destination = f"{hotel_name} ({hotel_city})" if hotel_name else hotel_city
            elif booking_type == "PACKAGE":
                # For packages, show destination + hotel
                dest = booking.get("destination", "")
                hotel_name = booking.get("hotel_name", "")
                destination = f"{dest} - {hotel_name}" if hotel_name else dest
            else:  # FLIGHT
                destination = booking.get("destination", "")
            
            self.table.setItem(row, 3, create_item(destination))
            
            # Column 4: Date (varies by type)
            if booking_type == "HOTEL":
                date = booking.get("check_in", "")
            elif booking_type == "PACKAGE":
                date = booking.get("depart_date", "")
            else:  # FLIGHT
                date = booking.get("depart_date", "")
            
            self.table.setItem(row, 4, create_item(date))
            
            # Column 5: Price
            self.table.setItem(row, 5, create_item(f"{booking.get('price', 0):.2f} €"))
            
            # Column 6: Status with color
            status = booking.get("status", "unknown")
            status_item = create_item(status.upper())
            if status == "confirmed":
                status_item.setForeground(QColor("#22c55e"))  # Green
            elif status == "cancelled":
                status_item.setForeground(QColor("#ef4444"))  # Red
            self.table.setItem(row, 6, status_item)

        self.table.setSortingEnabled(True)
        self.set_status(f"{len(bookings)} réservation(s) trouvée(s)")

