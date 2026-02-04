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

        # Connect view signals to presenter methods
        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)
        self.view.book_btn.clicked.connect(self.on_book)

    def on_search(self):
        """Handle search button click for hotels"""
        # Get IATA code from autocomplete widget (or text if not autocomplete)
        if hasattr(self.view.destination, 'get_iata_code'):
            destination = self.view.destination.get_iata_code()
        else:
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

        # Call real API endpoint for hotels with IATA code
        self.api.get_hotels_async(
            city_code=destination,
            on_success=self._on_hotels_received,
            on_error=self._on_search_error
        )

    def _on_hotels_received(self, hotels):
        """Callback when hotels are successfully retrieved from API"""
        self.last_hotels = hotels
        self.view.set_hotels(hotels)
        self.view.set_status(f"✅ {len(hotels)} hôtel(s) trouvé(s)")
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 RECHERCHER DES HÔTELS")

    def _on_search_error(self, error):
        """Callback when hotel search fails"""
        self.view.show_error(f"Erreur lors de la recherche: {str(error)}")
        self.view.set_status("")
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
            f"Hôtel: {data['name']}\\n"
            f"Prix: {data['price']}\\n\\n"
            f"Équipements: WiFi, Piscine, Spa\\n"
            f"Petit-déjeuner inclus\\n"
            f"Parking gratuit"
        )

    def on_book(self):
        """Handle book button click"""
        data = self.view.get_selected_hotel_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un hôtel.")
            return

        # Get check-in and check-out dates from view
        checkin = self.view.checkin_date.date().toString("yyyy-MM-dd")
        checkout = self.view.checkout_date.date().toString("yyyy-MM-dd")

        reply = QMessageBox.question(
            self.view,
            "Confirmation de réservation",
            f"Voulez-vous réserver cet hôtel ?\\n\\n"
            f"Hôtel: {data['name']}\\n"
            f"Prix: {data['price']}\\n"
            f"Check-in: {checkin}\\n"
            f"Check-out: {checkout}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Parse price from table display format 
                price_str = str(data['price']).replace("€", "").replace(",", ".").strip()
                price = float(price_str)
            except Exception as e:
                print(f"Error parsing price: {e}")
                self.view.show_error("Erreur lors de la lecture du prix.")
                return

            # Prepare booking payload matching BookHotelCommand
            payload = {
                "hotel_name": data['name'],
                "hotel_city": self.view.destination.text().strip(),
                "check_in": checkin,
                "check_out": checkout,
                "price": price,
                "adults": 1,  # Default to 1 adult (can be extended later)
                "user_id": SESSION.user_id,
                "user_name": SESSION.username
            }

            # Show loading state
            self.view.set_status("⏳ Réservation en cours...")
            self.view.book_btn.setEnabled(False)

            # Call async booking API
            self.api.book_hotel_async(
                booking_data=payload,
                on_success=self._on_book_success,
                on_error=self._on_book_error
            )

    def _on_book_success(self, result):
        """Callback for successful hotel booking"""
        self.view.set_status("✅ Hôtel réservé avec succès !")
        self.view.book_btn.setEnabled(True)
        
        booking_id = result.get('booking_id', 'N/A')
        QMessageBox.information(
            self.view,
            "Réservation réussie",
            f"Votre réservation d'hôtel a été confirmée avec succès !\\n\\n"
            f"ID de réservation: {booking_id}"
        )

    def _on_book_error(self, error):
        """Callback for failed hotel booking"""
        self.view.set_status("❌ Erreur de réservation")
        self.view.book_btn.setEnabled(True)
        self.view.show_error(f"Erreur lors de la réservation: {str(error)}")
