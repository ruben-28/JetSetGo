"""
City Autocomplete Widget
Custom QLineEdit with autocomplete functionality using Amadeus API
"""

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, QStringListModel, QTimer


class CityAutocompleteLineEdit(QLineEdit):
    """
    Custom QLineEdit with city/airport autocomplete.
    
    Features:
    - Real-time API search as user types
    - Dropdown suggestions with IATA codes
    - Stores selected IATA code for API calls
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.selected_iata_code = None
        self.city_data = {}  # Maps display text -> IATA code
        self._is_selecting = False  # Flag to prevent search during selection
        
        # Setup autocomplete
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)
        self.setCompleter(self.completer)
        
        # Model for suggestions
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        
        # Debounce timer to avoid too many API calls
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # Connect signals
        self.textChanged.connect(self._on_text_changed)
        self.completer.activated.connect(self._on_item_selected)
    
    def _on_text_changed(self, text):
        """Called when user types - debounced search"""
        # Don't search if we're programmatically setting text after selection
        if self._is_selecting:
            return
            
        if len(text) >= 2:
            # Restart timer (debounce)
            self.search_timer.stop()
            self.search_timer.start(300)  # Wait 300ms after last keystroke
        else:
            self.model.setStringList([])
            self.selected_iata_code = None
    
    def _perform_search(self):
        """Perform API search for cities"""
        keyword = self.text().strip()
        if len(keyword) < 2:
            return
        
        # Call async API
        self.api.search_cities_async(
            keyword=keyword,
            on_success=self._on_cities_received,
            on_error=self._on_search_error
        )
    
    def _on_cities_received(self, cities):
        """Callback when cities are received from API"""
        if not cities:
            self.model.setStringList([])
            return
        
        suggestions = []
        self.city_data = {}
        
        for city in cities:
            # Format: "Paris (PAR), France"
            iata = city.get('iata_code', '')
            name = city.get('name', 'Unknown')
            country = city.get('country', '')
            
            if iata:
                display_text = f"{name} ({iata}), {country}"
                suggestions.append(display_text)
                self.city_data[display_text] = iata
        
        # Update model
        self.model.setStringList(suggestions)
        
        # Show completer if not already visible
        if suggestions and not self.completer.popup().isVisible():
            self.completer.complete()
    
    def _on_search_error(self, error):
        """Callback when search fails"""
        print(f"City search error: {error}")
        self.model.setStringList([])
    
    def _on_item_selected(self, text):
        """Called when user selects an item from dropdown"""
        # Set flag to prevent textChanged from triggering search
        self._is_selecting = True
        
        # Extract IATA code from selection
        self.selected_iata_code = self.city_data.get(text)
        
        # Keep the display text in the field
        self.setText(text)
        
        # Clear suggestions to prevent re-showing
        self.model.setStringList([])
        
        # Reset flag after a brief delay
        QTimer.singleShot(100, lambda: setattr(self, '_is_selecting', False))
    
    def get_iata_code(self):
        """
        Get the IATA code for the selected/entered city.
        
        Returns:
            str: IATA code if available, otherwise the text as-is
        """
        if self.selected_iata_code:
            return self.selected_iata_code
        
        # If no selection, try to extract from current text
        text = self.text().strip()
        
        # Check if text matches a suggestion
        if text in self.city_data:
            return self.city_data[text]
        
        # Try to extract IATA from format "City (CODE), Country"
        if '(' in text and ')' in text:
            try:
                start = text.index('(') + 1
                end = text.index(')')
                code = text[start:end].strip()
                if len(code) == 3 and code.isalpha():
                    return code.upper()
            except:
                pass
        
        # Otherwise return the text as-is (let backend handle conversion)
        return text
    
    def clear(self):
        """Override clear to also reset IATA code"""
        super().clear()
        self.selected_iata_code = None
        self.city_data = {}
