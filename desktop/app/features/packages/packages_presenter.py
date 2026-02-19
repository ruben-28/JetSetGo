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
        
        # Set book handler for package cards
        self.view.set_book_handler(self.on_book)

    def on_search(self):
        """Handle search button click for packages"""
        # Get IATA codes
        if hasattr(self.view.origin, 'get_iata_code'):
            origin = self.view.origin.get_iata_code()
        else:
            origin = self.view.origin.text().strip()

        if hasattr(self.view.destination, 'get_iata_code'):
            destination = self.view.destination.get_iata_code()
        else:
            destination = self.view.destination.text().strip()
            
        checkin = self.view.checkin_date.date().toString("yyyy-MM-dd")
        checkout = self.view.checkout_date.date().toString("yyyy-MM-dd")
        adults = 1  # Default to 1 adult

        if not origin or not destination:
            self.view.show_error("Veuillez entrer une ville de départ et de destination.")
            return

        # Show loading state
        self.view.set_status("🔄 Recherche de packages en cours...")
        self.view.search_btn.setEnabled(False)
        self.view.search_btn.setText("⏳ Recherche...")
        self.view.clear_results()

        # Call API
        self.api.get_packages_async(
            origin=origin,
            destination=destination,
            depart_date=checkin,
            return_date=checkout,
            adults=adults,
            on_success=self._on_search_success,
            on_error=self._on_search_error
        )

    def _on_search_success(self, data):
        """Handle successful search results"""
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Packages")
        
        # Combine flights and hotels into "Packages" for display
        flights = data.get("flights", [])
        hotels = data.get("hotels", [])
        
        packages = []
        import itertools
        # Create combinations (up to 20)
        for i, (flight, hotel) in enumerate(itertools.product(flights, hotels)):
            if i >= 20: 
                break
            
            # Simple price addition
            total_price = flight.get("price", 0) + hotel.get("price", 0)
            
            pkg = {
                "id": f"{flight['id']}|{hotel['id']}",  # Compound ID
                "total_price": total_price,
                "flight": flight,
                "hotel": hotel
            }
            packages.append(pkg)

        self.last_packages = packages
        self.view.display_packages(packages)
        
        if not packages:
            self.view.show_error("Aucun package trouvé pour ces dates.")

    def _on_search_error(self, error):
        self.view.search_btn.setEnabled(True)
        self.view.search_btn.setText("🔍 Rechercher des Packages")
        self.view.show_error(f"Erreur de recherche: {str(error)}")
        self.view.set_status("❌ Erreur de recherche")

    def on_book(self, package_data: dict):
        """Handle book button click from package card"""
        flight = package_data.get("flight", {})
        hotel = package_data.get("hotel", {})
        total_price = package_data.get("total_price", 0)
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self.view,
            "Confirmation",
            f"Réserver ce package pour {total_price:.2f} € ?\n\n"
            f"✈️ Vol: {flight.get('airline', 'N/A')} - {flight.get('departure', '')} → {flight.get('destination', '')}\n"
            f"🏨 Hôtel: {hotel.get('name', 'N/A')} ({hotel.get('city', '')})\n\n"
            f"📅 Dates: {flight.get('depart_date', '')} - {flight.get('return_date', '')}",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.view.set_status("⏳ Réservation en cours...")
            
            # Prepare booking payload
            booking_payload = {
                "offer_id": flight.get('id', ''),
                "departure": flight.get('departure', ''),
                "destination": flight.get('destination', ''),
                "depart_date": flight.get('depart_date', ''),
                "return_date": flight.get('return_date', ''),
                "hotel_name": hotel.get('name', ''),
                "hotel_city": hotel.get('city', ''),
                "price": float(total_price),
                "adults": 1
            }
            
            self.api.book_package_async(
                booking_payload,
                on_success=self._on_book_success,
                on_error=self._on_book_error
            )

    def _on_book_success(self, result):
        self.view.show_success(f"✅ Réservation confirmée !\n\nID Trip: {result.get('trip_id', 'N/A')}")
        self.view.set_status("✅ Réservation réussie")

    def _on_book_error(self, error):
        self.view.show_error(f"❌ Erreur de réservation: {str(error)}")
        self.view.set_status("❌ Échec de la réservation")
