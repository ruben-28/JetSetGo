from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject
from services.session import SESSION


class FlightsPresenter(QObject):
    """
    Presenter for Flights View - handles business logic for flight searches
    """
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_offers = []

        # Connect view signals
        self.view.search_btn.clicked.connect(self.on_search)
        
        # Set book handler for flight cards
        self.view.set_book_handler(self.on_book)

    def on_search(self):
        """Handle search button click - async flight search"""
        # Get IATA codes from autocomplete widgets
        if hasattr(self.view.departure, 'get_iata_code'):
            departure = self.view.departure.get_iata_code()
        else:
            departure = self.view.departure.text().strip()
            
        if hasattr(self.view.destination, 'get_iata_code'):
            dest = self.view.destination.get_iata_code()
        else:
            dest = self.view.destination.text().strip()
            
        dep = self.view.depart_date.date().toString("yyyy-MM-dd")
        ret = self.view.return_date.date().toString("yyyy-MM-dd")

        if not departure or not dest:
            self.view.show_error("Veuillez remplir la ville de départ et la destination.")
            return

        # Show loading state
        self.view.set_status("🔄 Recherche en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")
        self.view.clear_results()

        # Call async API with IATA codes
        self.api.search_travel_async(
            departure, dest, dep, ret, None, None,
            on_success=self._on_search_success,
            on_error=self._on_search_error
        )

    def _on_search_success(self, offers):
        """Callback when search succeeds"""
        self.last_offers = offers
        self.view.display_flights(offers)
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Vols")

    def _on_search_error(self, error):
        """Callback when search fails"""
        self.view.show_error(str(error))
        self.view.set_status("❌ Erreur de recherche")
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Vols")

    def on_book(self, flight_data: dict):
        """Handle book button click from flight card"""
        airline = flight_data.get("airline", "N/A")
        price = flight_data.get("price", 0)
        departure = flight_data.get("departure", "")
        destination = flight_data.get("destination", "")
        
        reply = QMessageBox.question(
            self.view,
            "Confirmation",
            f"Réserver ce vol pour {price:.2f} € ?\n\n"
            f"✈️ Compagnie: {airline}\n"
            f"📍 {departure} → {destination}\n"
            f"📅 {flight_data.get('depart_date', '')} - {flight_data.get('return_date', '')}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            payload = {
                "offer_id": flight_data.get('id', ''),
                "departure": departure,
                "destination": destination,
                "depart_date": flight_data.get('depart_date', ''),
                "return_date": flight_data.get('return_date', ''),
                "price": float(price),
                "adults": 1,
                "user_id": SESSION.user_id,
                "user_name": SESSION.username
            }
            
            self.view.set_status("⏳ Réservation en cours...")

            self.api.book_flight_async(
                payload,
                on_success=self._on_book_success,
                on_error=self._on_book_error
            )

    def _on_book_success(self, result):
        """Callback for successful booking"""
        self.view.set_status("✅ Réservation confirmée !")
        QMessageBox.information(
            self.view, 
            "Réservation réussie", 
            f"Votre réservation a été confirmée avec succès !\n\nID: {result.get('booking_id', 'N/A')}"
        )

    def _on_book_error(self, error):
        """Callback for failed booking"""
        self.view.set_status("❌ Erreur de réservation")
        self.view.show_error(f"Erreur lors de la réservation : {str(error)}")
