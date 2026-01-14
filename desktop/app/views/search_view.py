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
        
        # History button - Mes Voyages
        self.history_btn = QPushButton("🧳 Mes Voyages")
        self.history_btn.setObjectName("iconButton")
        self.history_btn.setMinimumHeight(40)
        self.history_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.history_btn)
        
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
        self.departure.setPlaceholderText("Départ")
        self.departure.setMinimumHeight(48)
        form_row.addWidget(self.departure)
        
        # Destination
        self.destination = QLineEdit()
        self.destination.setPlaceholderText("Destination")
        self.destination.setMinimumHeight(48)
        form_row.addWidget(self.destination)
        
        # Departure date - Calendar picker with label
        depart_date_label = QLabel("📅 Départ:")
        depart_date_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(depart_date_label)
        
        self.depart_date = QDateEdit()
        self.depart_date.setCalendarPopup(True)
        self.depart_date.setDate(QDate.currentDate().addDays(7))  # Default to 1 week from now
        self.depart_date.setDisplayFormat("yyyy-MM-dd")
        self.depart_date.setMinimumHeight(48)
        self.depart_date.setMinimumWidth(130)
        form_row.addWidget(self.depart_date)
        
        # Return date - Calendar picker with label
        return_date_label = QLabel("📅 Retour:")
        return_date_label.setStyleSheet("color: #0077b6; font-weight: 600; font-size: 12px;")
        form_row.addWidget(return_date_label)
        
        self.return_date = QDateEdit()
        self.return_date.setCalendarPopup(True)
        self.return_date.setDate(QDate.currentDate().addDays(14))  # Default to 2 weeks from now
        self.return_date.setDisplayFormat("yyyy-MM-dd")
        self.return_date.setMinimumHeight(48)
        self.return_date.setMinimumWidth(130)
        form_row.addWidget(self.return_date)
        
        # Passengers
        self.passengers = QComboBox()
        self.passengers.addItems(["1 Pass.", "2 Pass.", "3 Pass.", "4 Pass.", "5+ Pass."])
        self.passengers.setMinimumHeight(48)
        form_row.addWidget(self.passengers)
        
        # Budget
        self.budget = QLineEdit()
        self.budget.setPlaceholderText("Budget")
        self.budget.setMinimumHeight(48)
        form_row.addWidget(self.budget)
        
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
        self.table.setMinimumHeight(200)
        self.table.setMaximumHeight(400)  # Limit height to ensure buttons are visible
        
        # Disable gridlines to prevent white line artifact
        self.table.setShowGrid(False)
        # Disable focus rectangle
        self.table.setFocusPolicy(Qt.NoFocus)
        
        # Configure header font to prevent strikethrough
        from PySide6.QtGui import QFont
        header_font = self.table.horizontalHeader().font()
        header_font.setStrikeOut(False)
        header_font.setUnderline(False)
        self.table.horizontalHeader().setFont(header_font)
        
        # Configure table font
        table_font = self.table.font()
        table_font.setStrikeOut(False)
        table_font.setUnderline(False)
        self.table.setFont(table_font)
        
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
        actions_frame.setFixedHeight(75)  # Fixed height to ensure visibility
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(15, 10, 15, 10)
        actions_layout.setSpacing(15)
        
        self.details_btn = QPushButton("🔍 Voir détails")
        self.details_btn.setObjectName("secondary")
        self.details_btn.setEnabled(False)
        self.details_btn.setMinimumHeight(52)
        self.details_btn.setMinimumWidth(180)
        self.details_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(self.details_btn)

        self.book_btn = QPushButton("✈️ RÉSERVER CE VOL")
        self.book_btn.setEnabled(False)
        self.book_btn.setMinimumHeight(52)
        self.book_btn.setMinimumWidth(220)
        self.book_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(self.book_btn)

        actions_layout.addStretch()
        main_layout.addWidget(actions_frame)

        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        count = len(self.table.selectedItems())
        has_selection = count > 0
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
        # Disable sorting while updating to prevent index issues
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for offer in offers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Helper to create items with consistent styling
            def create_item(text):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor("#24292f"))  # Dark grey text
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                # Make item read-only to stabilize selection rendering
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                # Ensure no strikethrough
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

        # Re-enable sorting
        self.table.setSortingEnabled(True)
        
        self.set_status(f"✨ {len(offers)} vol(s) trouvé(s)")

    def get_selected_flight_data(self):
        """Get data from the currently selected flight row."""
        selection_model = self.table.selectionModel()
        current_index = selection_model.currentIndex()
        row = current_index.row()
        
        if row < 0:
            return None
        
        # Get items from each column
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

