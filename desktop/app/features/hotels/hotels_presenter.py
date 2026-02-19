from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject
from services.session import SESSION


class HotelsPresenter(QObject):
    """
    Presenter for Hotels View - handles business logic for hotel searches
    """
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_hotels = []

        # Connect view signals
        self.view.search_btn.clicked.connect(self.on_search)
        
        # Set book handler for hotel cards
        self.view.set_book_handler(self.on_book)

    def on_search(self):
        """Handle search button click for hotels"""
        # Get IATA code from autocomplete widget
        if hasattr(self.view.destination, 'get_iata_code'):
            destination = self.view.destination.get_iata_code()
        else:
            destination = self.view.destination.text().strip()
            
        checkin = self.view.checkin_date.date().toString("yyyy-MM-dd")
        checkout = self.view.checkout_date.date().toString("yyyy-MM-dd")

        if not destination:
            self.view.show_error("Veuillez entrer une destination.")
            return

        # Show loading state
        self.view.set_status("🔄 Recherche d'hôtels en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")
        self.view.clear_results()

        # Call real API endpoint for hotels with IATA code
        self.api.get_hotels_async(
            city_code=destination,
            on_success=self._on_hotels_received,
            on_error=self._on_search_error
        )

    def _on_hotels_received(self, hotels):
        """Callback when hotels are successfully retrieved from API"""
        self.last_hotels = hotels
        self.view.display_hotels(hotels)
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Hôtels")

    def _on_search_error(self, error):
        """Callback when hotel search fails"""
        self.view.show_error(f"Erreur lors de la recherche: {str(error)}")
        self.view.set_status("❌ Erreur de recherche")
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Hôtels")

    def on_book(self, hotel_data: dict):
        """Handle book button click from hotel card"""
        name = hotel_data.get("name", "N/A")
        price = hotel_data.get("price", 0)
        location = hotel_data.get("location", hotel_data.get("city", ""))
        
        # Get check-in and check-out dates from view
        checkin = self.view.checkin_date.date().toString("yyyy-MM-dd")
        checkout = self.view.checkout_date.date().toString("yyyy-MM-dd")

        reply = QMessageBox.question(
            self.view,
            "Confirmation",
            f"Réserver cet hôtel pour {price:.2f} € ?\n\n"
            f"🏨 Hôtel: {name}\n"
            f"📍 Lieu: {location}\n"
            f"📅 {checkin} - {checkout}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Get IATA code from autocomplete widget
            if hasattr(self.view.destination, 'get_iata_code'):
                hotel_city = self.view.destination.get_iata_code()
            else:
                hotel_city = self.view.destination.text().strip()

            # Prepare booking payload
            payload = {
                "hotel_name": name,
                "hotel_city": hotel_city,
                "check_in": checkin,
                "check_out": checkout,
                "price": float(price),
                "adults": 1,
                "user_id": SESSION.user_id,
                "user_name": SESSION.username
            }

            # Show loading state
            self.view.set_status("⏳ Réservation en cours...")

            # Call async booking API
            self.api.book_hotel_async(
                booking_data=payload,
                on_success=self._on_book_success,
                on_error=self._on_book_error
            )

    def _on_book_success(self, result):
        """Callback for successful hotel booking"""
        self.view.set_status("✅ Hôtel réservé avec succès !")
        
        booking_id = result.get('booking_id', 'N/A')
        QMessageBox.information(
            self.view,
            "Réservation réussie",
            f"Votre réservation d'hôtel a été confirmée avec succès !\n\n"
            f"ID de réservation: {booking_id}"
        )

    def _on_book_error(self, error):
        """Callback for failed hotel booking"""
        self.view.set_status("❌ Erreur de réservation")
        self.view.show_error(f"Erreur lors de la réservation: {str(error)}")
