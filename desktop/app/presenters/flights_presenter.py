from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject
from services.session import SESSION


class FlightsPresenter(QObject):
    """
    Presenter for Flights View - handles business logic for flight searches
    (Reuses logic from search_presenter.py)
    """
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_offers = []

        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)
        self.view.book_btn.clicked.connect(self.on_book)

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
            self.view.show_error("Remplis ville de départ et destination.")
            return
        
        # Map stops filter to max_stops parameter
        stops_filter = self.view.stops_filter.currentText()
        max_stops = None  # Default: all flights
        if stops_filter == "Direct uniquement":
            max_stops = 0
        elif stops_filter == "Maximum 1 escale":
            max_stops = 1

        # Show loading state
        self.view.set_status("🔄 Recherche en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")

        # Call async API with IATA codes and max_stops (no budget)
        self.api.search_travel_async(
            departure, dest, dep, ret, None, max_stops,
            on_success=self._on_search_success,
            on_error=self._on_search_error
        )

    def _on_search_success(self, offers):
        """Callback when search succeeds"""
        self.last_offers = offers
        self.view.set_offers(offers)
        self.view.set_status(f"✅ {len(offers)} offres trouvées")
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 RECHERCHER DES VOLS")

    def _on_search_error(self, error):
        """Callback when search fails"""
        self.view.show_error(str(error))
        self.view.set_status("")
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 RECHERCHER DES VOLS")

    def on_details(self):
        """Handle details button click - async with visual locking"""
        if hasattr(self, '_details_loading') and self._details_loading:
            return
        
        selection_model = self.view.table.selectionModel()
        current_index = selection_model.currentIndex()
        row = current_index.row()
        
        if row < 0:
            return
        
        offer_id_item = self.view.table.item(row, 0)
        if not offer_id_item:
            return
        
        offer_id = offer_id_item.text()

        # Set loading state
        self._details_loading = True
        self.view.details_btn.setEnabled(False)
        self.view.details_btn.setText("⏳...")

        # Call async API
        self.api.travel_details_async(
            offer_id,
            on_success=lambda d: self._show_details(offer_id, d),
            on_error=lambda e: self._on_details_error(e)
        )

    def _show_details(self, offer_id, details):
        """Show details dialog and restore button state"""
        self._details_loading = False
        self.view.details_btn.setText("🔍 Voir détails")
        self.view.details_btn.setEnabled(True)
        
        QMessageBox.information(
            self.view,
            f"Détails {offer_id}",
            f"Bagage: {details.get('baggage')}\\n"
            f"Remboursement: {details.get('refund_policy')}\\n"
            f"Hôtel: {details.get('hotel_suggestion', {}).get('name')}"
        )

    def _on_details_error(self, error):
        """Handle details error and restore button state"""
        self._details_loading = False
        self.view.details_btn.setText("🔍 Voir détails")
        self.view.details_btn.setEnabled(True)
        self.view.show_error(str(error))

    def on_book(self):
        """Handle book button click"""
        data = self.view.get_selected_flight_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un vol.")
            return

        reply = QMessageBox.question(
            self.view,
            "Confirmation de réservation",
            f"Voulez-vous réserver ce vol pour {self.view.destination.text()} ?\\n\\n"
            f"Compagnie: {data['airline']}\\n"
            f"Prix: {data['price']}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                pass_text = self.view.passengers.currentText()
                num_tickets = int(pass_text.split()[0])
                
                price_str = data['price'].replace("€", "").replace(",", ".").strip()
                price = float(price_str)
            except Exception as e:
                print(f"Error parsing booking data: {e}")
                self.view.show_error("Erreur lors de la lecture des données du vol.")
                return

            payload = {
                "offer_id": data['id'],
                "departure": self.view.departure.text().strip(),
                "destination": self.view.destination.text().strip(),
                "depart_date": self.view.depart_date.date().toString("yyyy-MM-dd"),
                "return_date": self.view.return_date.date().toString("yyyy-MM-dd"),
                "price": price,
                "adults": num_tickets,
                "user_id": SESSION.user_id,
                "user_name": SESSION.username
            }
            
            self.view.set_status("⏳ Réservation en cours...")
            self.view.book_btn.setEnabled(False)

            self.api.book_flight_async(
                payload,
                on_success=self._on_book_success,
                on_error=self._on_book_error
            )

    def _on_book_success(self, result):
        """Callback for successful booking"""
        self.view.set_status("✅ Réservation confirmée !")
        self.view.book_btn.setEnabled(True)
        QMessageBox.information(
            self.view, 
            "Réservation réussie", 
            "Votre réservation a été confirmée avec succès !"
        )

    def _on_book_error(self, error):
        """Callback for failed booking"""
        self.view.set_status("❌ Erreur de réservation")
        self.view.book_btn.setEnabled(True)
        self.view.show_error(f"Erreur lors de la réservation : {str(error)}")
