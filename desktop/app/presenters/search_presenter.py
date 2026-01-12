from PySide6.QtWidgets import QMessageBox

class SearchPresenter:
    def __init__(self, view, api_client):
        self.view = view
        self.api = api_client
        self.last_offers = []

        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)

    def on_search(self):
        """Handle search button click - now async, won't freeze UI"""
        departure = self.view.departure.text().strip()
        dest = self.view.destination.text().strip()
        dep = self.view.depart_date.text().strip()
        ret = self.view.return_date.text().strip()
        bud_txt = self.view.budget.text().strip()

        if not departure or not dest or not dep or not ret:
            self.view.show_error("Remplis ville de départ, destination + dates (YYYY-MM-DD).")
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
        """Handle details button click - now async"""
        items = self.view.table.selectedItems()
        if not items:
            return
        
        # Get offer ID from first column (more robust)
        row = self.view.table.currentRow()
        if row < 0:
            return
        
        offer_id_item = self.view.table.item(row, 0)
        if not offer_id_item:
            return
        
        offer_id = offer_id_item.text()

        # Call async API
        self.api.travel_details_async(
            offer_id,
            on_success=lambda d: self._show_details(offer_id, d),
            on_error=lambda e: self.view.show_error(str(e))
        )

    def _show_details(self, offer_id, details):
        """Show details dialog"""
        QMessageBox.information(
            self.view,
            f"Détails {offer_id}",
            f"Bagage: {details.get('baggage')}\n"
            f"Remboursement: {details.get('refund_policy')}\n"
            f"Hôtel: {details.get('hotel_suggestion', {}).get('name')}"
        )

