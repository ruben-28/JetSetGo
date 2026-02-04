from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject


class PackagesPresenter(QObject):
    """
    Presenter for Packages View - handles business logic for package searches
    """
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_packages = []

        # Connect view signals to presenter methods
        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)
        self.view.book_btn.clicked.connect(self.on_book)

    def on_search(self):
        """Handle search button click for packages"""
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
        self.view.set_status("🔄 Recherche de packages en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")

        # For now, show mock data (you can integrate with API later)
        # TODO: Call API endpoint for packages when available
        self._show_mock_packages(destination)

    def _show_mock_packages(self, destination):
        """Show mock package data (replace with real API call later)"""
        mock_packages = [
            {
                "id": "PKG001",
                "name": f"Package {destination} Découverte",
                "price": 799,
                "hotel": "Hôtel Premium 4★",
                "flight": "Vol A/R inclus",
                "duration_days": 7,
                "score": 4.5
            },
            {
                "id": "PKG002",
                "name": f"Package {destination} Luxe",
                "price": 1299,
                "hotel": "Resort 5★",
                "flight": "Vol Business A/R",
                "duration_days": 7,
                "score": 4.8
            },
            {
                "id": "PKG003",
                "name": f"Package {destination} Économique",
                "price": 499,
                "hotel": "Hôtel Confort 3★",
                "flight": "Vol Eco A/R",
                "duration_days": 5,
                "score": 4.2
            }
        ]
        
        self.last_packages = mock_packages
        self.view.set_packages(mock_packages)
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 RECHERCHER DES PACKAGES")

    def on_details(self):
        """Handle details button click"""
        data = self.view.get_selected_package_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un package.")
            return

        QMessageBox.information(
            self.view,
            f"Détails {data['id']}",
            f"Package: {data['name']}\n"
            f"Prix: {data['price']}\n\n"
            f"Inclus: Hôtel + Vol + Transferts\n"
            f"Petit-déjeuner inclus\n"
            f"Annulation flexible"
        )

    def on_book(self):
        """Handle book button click"""
        data = self.view.get_selected_package_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un package.")
            return

        reply = QMessageBox.question(
            self.view,
            "Confirmation de réservation",
            f"Voulez-vous réserver ce package ?\\n\\n"
            f"Package: {data['name']}\\n"
            f"Prix: {data['price']}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # TODO: Integrate with actual booking API
            self.view.show_info("Réservation confirmée ! (Mode démo)")
            self.view.set_status("✅ Package réservé avec succès !")
