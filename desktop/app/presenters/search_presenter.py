from PySide6.QtWidgets import QMessageBox

class SearchPresenter:
    def __init__(self, view, api_client):
        self.view = view
        self.api = api_client
        self.last_offers = []

        self.view.search_btn.clicked.connect(self.on_search)
        self.view.details_btn.clicked.connect(self.on_details)

    def on_search(self):
        dest = self.view.destination.text().strip()
        dep = self.view.depart_date.text().strip()
        ret = self.view.return_date.text().strip()
        bud_txt = self.view.budget.text().strip()

        if not dest or not dep or not ret:
            self.view.show_error("Remplis destination + dates (YYYY-MM-DD).")
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

        self.view.set_status("Recherche en cours...")
        self.view.search_btn.setEnabled(False)

        try:
            offers = self.api.search_travel(dest, dep, ret, budget)
            self.last_offers = offers
            self.view.set_offers(offers)
            self.view.set_status(f"{len(offers)} offres trouvées")
        except Exception as e:
            self.view.show_error(str(e))
            self.view.set_status("")
        finally:
            self.view.search_btn.setEnabled(True)

    def on_details(self):
        items = self.view.table.selectedItems()
        if not items:
            return
        offer_id = items[0].text()

        try:
            d = self.api.travel_details(offer_id)
            QMessageBox.information(
                self.view,
                f"Détails {offer_id}",
                f"Bagage: {d.get('baggage')}\n"
                f"Remboursement: {d.get('refund_policy')}\n"
                f"Hôtel: {d.get('hotel_suggestion', {}).get('name')}"
            )
        except Exception as e:
            self.view.show_error(str(e))
