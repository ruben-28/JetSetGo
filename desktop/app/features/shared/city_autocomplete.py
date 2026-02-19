"""
Widget d'Autocomplétion de Ville
QLineEdit personnalisé avec fonctionnalité d'autocomplétion utilisant l'API Amadeus
"""

from PySide6.QtWidgets import QLineEdit, QCompleter
from PySide6.QtCore import Qt, QStringListModel, QTimer


class CityAutocompleteLineEdit(QLineEdit):
    """
    QLineEdit personnalisé avec autocomplétion ville/aéroport.
    
    Fonctionnalités :
    - Recherche API en temps réel lors de la frappe
    - Suggestions déroulantes avec codes IATA
    - Stocke le code IATA sélectionné pour les appels API
    """
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.selected_iata_code = None
        self.city_data = {}  # Mappe texte d'affichage -> code IATA
        self._is_selecting = False  # Drapeau pour empêcher la recherche pendant la sélection
        
        # Setup completer
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)
        self.setCompleter(self.completer)
        
        # Modèle pour suggestions
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        
        # Timer de debounce pour éviter trop d'appels API
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        # Connect signals
        self.textChanged.connect(self._on_text_changed)
        self.completer.activated.connect(self._on_item_selected)
    
    def _on_text_changed(self, text):
        """Appelé lors de la frappe - recherche avec debounce"""
        # Ne pas chercher si on définit le texte programmatiquement après sélection
        if self._is_selecting:
            return
            
        if len(text) >= 2:
            # Redémarrer timer (debounce)
            self.search_timer.stop()
            self.search_timer.start(300)  # Attendre 300ms après la dernière frappe
        else:
            self.model.setStringList([])
            self.selected_iata_code = None
    
    def _perform_search(self):
        """Exécuter la recherche API pour les villes"""
        keyword = self.text().strip()
        if len(keyword) < 2:
            return
        
        # Appel API asynchrone
        self.api.search_cities_async(
            keyword=keyword,
            on_success=self._on_cities_received,
            on_error=self._on_search_error
        )
    
    def _on_cities_received(self, cities):
        """Callback lorsque les villes sont reçues de l'API"""
        if not cities:
            self.model.setStringList([])
            return
        
        suggestions = []
        self.city_data = {}
        
        for city in cities:
            # Format: "Paris (PAR), France"
            iata = city.get('iata_code', '')
            name = city.get('name', 'Inconnu')
            country = city.get('country', '')
            
            if iata:
                display_text = f"{name} ({iata}), {country}"
                suggestions.append(display_text)
                self.city_data[display_text] = iata
        
        # Mettre à jour le modèle
        self.model.setStringList(suggestions)
        
        # Afficher le completer s'il n'est pas déjà visible
        if suggestions and not self.completer.popup().isVisible():
            self.completer.complete()
    
    def _on_search_error(self, error):
        """Callback lors de l'échec de la recherche"""
        print(f"Erreur recherche ville: {error}")
        self.model.setStringList([])
    
    def _on_item_selected(self, text):
        """Appelé lorsque l'utilisateur sélectionne un élément du menu déroulant"""
        # Définir le drapeau pour empêcher textChanged de déclencher une recherche
        self._is_selecting = True
        
        # Extraire le code IATA de la sélection
        self.selected_iata_code = self.city_data.get(text)
        
        # Garder le texte d'affichage dans le champ
        self.setText(text)
        
        # Effacer les suggestions pour empêcher le réaffichage
        self.model.setStringList([])
        
        # Réinitialiser le drapeau après un court délai
        QTimer.singleShot(100, lambda: setattr(self, '_is_selecting', False))
    
    def get_iata_code(self):
        """
        Récupère le code IATA pour la ville sélectionnée/saisie.
        
        Retourne:
            str: Code IATA si disponible, sinon le texte tel quel
        """
        if self.selected_iata_code:
            return self.selected_iata_code
        
        # Si pas de sélection, essayer d'extraire du texte actuel
        text = self.text().strip()
        
        # Vérifier si le texte correspond à une suggestion
        if text in self.city_data:
            return self.city_data[text]
        
        # Essayer d'extraire IATA du format "City (CODE), Country"
        if '(' in text and ')' in text:
            try:
                start = text.index('(') + 1
                end = text.index(')')
                code = text[start:end].strip()
                if len(code) == 3 and code.isalpha():
                    return code.upper()
            except:
                pass
        
        # Sinon retourner le texte tel quel (laisser le backend gérer la conversion)
        return text
    
    def clear(self):
        """Surcharge clear pour réinitialiser aussi le code IATA"""
        super().clear()
        self.selected_iata_code = None
        self.city_data = {}
