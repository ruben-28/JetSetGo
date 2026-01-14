from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QObject
from services.session import SESSION

class SearchPresenter(QObject):
    def __init__(self, view, api_client):
        super().__init__()
        self.view = view
        self.api = api_client
        self.last_offers = []

        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)
        self.view.book_btn.clicked.connect(self.on_book)

    def on_search(self):
        """Handle search button click - now async, won't freeze UI"""
        departure = self.view.departure.text().strip()
        dest = self.view.destination.text().strip()
        dep = self.view.depart_date.date().toString("yyyy-MM-dd")
        ret = self.view.return_date.date().toString("yyyy-MM-dd")
        bud_txt = self.view.budget.text().strip()

        if not departure or not dest:
            self.view.show_error("Remplis ville de départ et destination.")
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
        self.view.set_status("🔄 Recherche en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")

        # Call async API (won't freeze UI!)
        self.api.search_travel_async(
            departure, dest, dep, ret, budget,
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
        """Handle details button click - now async with visual locking"""
        # Guard: prevent duplicate calls while loading
        if hasattr(self, '_details_loading') and self._details_loading:
            return
        
        # Use selectionModel for more robust row detection
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
        # Reset loading state
        self._details_loading = False
        self.view.details_btn.setText("🔍 Voir détails")
        self.view.details_btn.setEnabled(True)
        
        QMessageBox.information(
            self.view,
            f"Détails {offer_id}",
            f"Bagage: {details.get('baggage')}\n"
            f"Remboursement: {details.get('refund_policy')}\n"
            f"Hôtel: {details.get('hotel_suggestion', {}).get('name')}"
        )

    def _on_details_error(self, error):
        """Handle details error and restore button state"""
        # Reset loading state
        self._details_loading = False
        self.view.details_btn.setText("🔍 Voir détails")
        self.view.details_btn.setEnabled(True)
        self.view.show_error(str(error))

    def on_book(self):
        """Handle book button click"""
        # 1. Get selected data from view
        data = self.view.get_selected_flight_data()
        if not data:
            self.view.show_error("Veuillez sélectionner un vol.")
            return

        # 2. Confirmation Dialog
        reply = QMessageBox.question(
            self.view,
            "Confirmation de réservation",
            f"Voulez-vous réserver ce vol pour {self.view.destination.text()} ?\n\n"
            f"Compagnie: {data['airline']}\n"
            f"Prix: {data['price']}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 3. Prepare payload matching BookFlightCommand
            try:
                # Extract number of seats (e.g., "1 Pass." -> 1)
                pass_text = self.view.passengers.currentText()
                num_tickets = int(pass_text.split()[0])
                
                # Clean price string (e.g., "150 €" -> 150.0)
                price_str = data['price'].replace("€", "").replace(",", ".").strip()
                price = float(price_str)
            except Exception as e:
                print(f"Error parsing booking data: {e}")
                self.view.show_error("Erreur lors de la lecture des données du vol.")
                return

            # Construct payload exactly as backend BookFlightCommand expects
            payload = {
                "offer_id": data['id'],  # String ID
                "departure": self.view.departure.text().strip(),
                "destination": self.view.destination.text().strip(),
                "depart_date": self.view.depart_date.date().toString("yyyy-MM-dd"),
                "return_date": self.view.return_date.date().toString("yyyy-MM-dd"),
                "price": price,
                "adults": num_tickets,
                "user_id": SESSION.user_id,
                "user_name": SESSION.username
            }
            
            # Show loading
            self.view.set_status("⏳ Réservation en cours...")
            self.view.book_btn.setEnabled(False)

            # 4. Call API
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
