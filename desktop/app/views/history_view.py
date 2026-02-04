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
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Destination", "Date de départ", "Prix (€)", "Statut"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Configure column widths
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
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
            
            # Short ID (first 8 chars)
            short_id = booking.get("id", "")[:8] + "..."
            self.table.setItem(row, 0, create_item(short_id))
            self.table.setItem(row, 1, create_item(booking.get("destination", "")))
            self.table.setItem(row, 2, create_item(booking.get("depart_date", "")))
            self.table.setItem(row, 3, create_item(f"{booking.get('price', 0):.2f} €"))
            
            # Status with color
            status = booking.get("status", "unknown")
            status_item = create_item(status.upper())
            if status == "confirmed":
                status_item.setForeground(QColor("#22c55e"))  # Green
            elif status == "cancelled":
                status_item.setForeground(QColor("#ef4444"))  # Red
            self.table.setItem(row, 4, status_item)

        self.table.setSortingEnabled(True)
        self.set_status(f"{len(bookings)} réservation(s) trouvée(s)")
