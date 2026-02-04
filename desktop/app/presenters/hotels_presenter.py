from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject


class HotelsPresenter(QObject):
    """
    Presenter for Hotels View - handles business logic for hotel searches
    """
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_hotels = []

        # Connect view signals to presenter methods
        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)
        self.view.book_btn.clicked.connect(self.on_book)

    def on_search(self):
        """Handle search button click for hotels"""
        destination = self.view.destination.text().strip()
        checkin = self.view.checkin_date.date().toString("yyyy-MM-dd")
        checkout = self.view.checkout_date.date().toString("yyyy-MM-dd")
        bud_txt = self.view.budget.text().strip()

        if not destination:
            self.view.show_error("Veuillez entrer une destination.")
            return

        budget = None
        if bud_txt:
            try:
                budget = int(bud_txt)
                if budget < 0:
                    raise ValueError()
            except Exception:
                self.view.show_error("Budget invalide (nombre positif).")
                return

        # Show loading state
        self.view.set_status("🔄 Recherche d'hôtels en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")

        # For now, show mock data (you can integrate with Amadeus hotel API later)
        # TODO: Call API endpoint for hotels when available
        self._show_mock_hotels(destination)

    def _show_mock_hotels(self, destination):
        """Show mock hotel data (replace with real API call later)"""
        mock_hotels = [
            {
                "id": "HTL001",
                "name": f"Grand Hotel {destination}",
                "price": 120,
                "stars": 4,
                "location": "Centre-ville",
                "score": 4.5
            },
            {
                "id": "HTL002",
                "name": f"Luxury Resort {destination}",
                "price": 250,
                "stars": 5,
                "location": "Bord de mer",
                "score": 4.8
            },
            {
                "id": "HTL003",
                "name": f"Budget Inn {destination}",
                "price": 60,
                "stars": 3,
                "location": "Proche centre",
                "score": 4.0
            },
            {
                "id": "HTL004",
                "name": f"Boutique Hotel {destination}",
                "price": 180,
                "stars": 4,
                "location": "Quartier historique",
                "score": 4.6
            }
        ]
        
        self.last_hotels = mock_hotels
        self.view.set_hotels(mock_hotels)
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 RECHERCHER DES HÔTELS")

    def on_details(self):
        """Handle details button click"""
        data = self.view.get_selected_hotel_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un hôtel.")
            return

        QMessageBox.information(
            self.view,
            f"Détails {data['id']}",
            f"Hôtel: {data['name']}\n"
            f"Prix: {data['price']}\n\n"
            f"Équipements: WiFi, Piscine, Spa\n"
            f"Petit-déjeuner inclus\n"
            f"Parking gratuit"
        )

    def on_book(self):
        """Handle book button click"""
        data = self.view.get_selected_hotel_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un hôtel.")
            return

        reply = QMessageBox.question(
            self.view,
            "Confirmation de réservation",
            f"Voulez-vous réserver cet hôtel ?\\n\\n"
            f"Hôtel: {data['name']}\\n"
            f"Prix: {data['price']}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # TODO: Integrate with actual hotel booking API
            self.view.show_info("Réservation confirmée ! (Mode démo)")
            self.view.set_status("✅ Hôtel réservé avec succès !")
