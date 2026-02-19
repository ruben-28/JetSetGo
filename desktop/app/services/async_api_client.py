"""
Client API Asynchrone pour l'application Desktop
Utilise httpx pour les requêtes HTTP asynchrones afin d'éviter le gel de l'UI.
"""

import httpx
from typing import Optional
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class ApiTaskSignals(QObject):
    """
    Signaux pour la communication entre ApiTask et le thread principal.
    Les signaux Qt sont thread-safe et automatiquement mis en file d'attente vers le thread principal.
    """
    finished = Signal(object)  # Émet les données de résultat
    error = Signal(Exception)  # Émet l'exception en cas d'erreur


class ApiTask(QRunnable):
    """
    Tâche exécutable (Runnable) pour les appels API asynchrones.
    S'exécute dans un thread d'arrière-plan pour éviter de bloquer l'UI.
    Utilise des signaux pour des callbacks thread-safe.
    """
    
    def __init__(self, func, callback, error_callback):
        super().__init__()
        self.func = func
        self.signals = ApiTaskSignals()
        self.setAutoDelete(False)  # Empêcher la suppression avant la livraison du signal
        
        # Connecter les signaux aux callbacks avec QueuedConnection pour la sécurité des threads
        from PySide6.QtCore import Qt
        if callback:
            self.signals.finished.connect(callback, Qt.QueuedConnection)
        if error_callback:
            self.signals.error.connect(error_callback, Qt.QueuedConnection)
    
    def run(self):
        """Exécute la fonction asynchrone dans un thread d'arrière-plan"""
        import asyncio
        try:
            # Créer une nouvelle boucle d'événements pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.func())
            loop.close()
            
            # Émettre le résultat via signal (thread-safe !)
            self.signals.finished.emit(result)
        except Exception as e:
            # Émettre l'erreur via signal (thread-safe !)
            self.signals.error.emit(e)


class AsyncApiClient(QObject):
    """
    Client API asynchrone qui ne gèle pas l'UI.
    Utilise QThreadPool pour exécuter les opérations asynchrones en arrière-plan.
    """
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.thread_pool = QThreadPool()
        self.token = None  # Sera défini après la connexion
        self._http_client: Optional[httpx.AsyncClient] = None  # Client persistant
    
    def set_token(self, token: str):
        """Définit le token d'authentification"""
        self.token = token
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Obtient ou crée un client HTTP persistant (initialisation différée)"""
        if self._http_client is None or self._http_client.is_closed:
            # Augmenter le timeout à 130s pour gérer les requêtes IA longues (backend timeout est 120s)
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(130.0))
        return self._http_client
    
    async def close(self):
        """Ferme le client HTTP - appeler à la fermeture de l'application"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    def _get_headers(self) -> dict:
        """Obtient les en-têtes avec authentification si le token est défini"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    # ========================================================================
    # Méthodes API Asynchrones
    # ========================================================================
    
    def register_async(self, username: str, email: str, password: str, 
                      on_success, on_error):
        """Inscription utilisateur (async, non-bloquant)"""
        async def _register():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/register",
                    json={"username": username, "email": email, "password": password},
                    timeout=10.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_register, on_success, on_error)
        self.thread_pool.start(task)
    
    def login_async(self, username_or_email: str, password: str,
                   on_success, on_error):
        """Connexion utilisateur (async, non-bloquant)"""
        async def _login():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json={"username_or_email": username_or_email, "password": password},
                    timeout=10.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_login, on_success, on_error)
        self.thread_pool.start(task)
    
    def search_travel_async(self, departure: str, destination: str,
                           depart_date: str, return_date: str,
                           budget: Optional[int], max_stops: Optional[int] = None,
                           on_success=None, on_error=None):
        """Recherche d'offres de voyage (async, non-bloquant)"""
        async def _search():
            params = {
                "departure": departure,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
            }
            if budget is not None:
                params["budget"] = budget
            if max_stops is not None:
                params["max_stops"] = max_stops
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/search",
                    params=params,
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_search, on_success, on_error)
        self.thread_pool.start(task)
    
    def travel_details_async(self, offer_id: str, on_success, on_error):
        """Récupère les détails d'une offre (async, non-bloquant)"""
        async def _details():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/details/{offer_id}",
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_details, on_success, on_error)
        self.thread_pool.start(task)

    def get_packages_async(self, origin: str, destination: str, 
                          depart_date: str, return_date: str, adults: int,
                          on_success, on_error):
        """Recherche de packages (async, non-bloquant) - Requête POST"""
        async def _search_packages():
            payload = {
                "origin": origin,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
                "adults": adults
            }
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/travel/packages/search",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=25.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_search_packages, on_success, on_error)
        self.thread_pool.start(task)

    def book_package_async(self, booking_data: dict, on_success, on_error):
        """Réserver un package (async, non-bloquant)"""
        async def _book_package():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/travel/book/package",
                    json=booking_data,
                    headers=self._get_headers(),
                    timeout=20.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_book_package, on_success, on_error)
        self.thread_pool.start(task)

    def get_hotels_async(self, city_code: str, on_success, on_error):
        """Récupérer des hôtels (async, non-bloquant)"""
        async def _get_hotels():
            params = {"city_code": city_code}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/hotels",
                    params=params,
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_get_hotels, on_success, on_error)
        self.thread_pool.start(task)

    def book_flight_async(self, booking_data: dict, on_success, on_error):
        """Réserver un vol (async, non-bloquant)"""
        async def _book():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/travel/book",
                    json=booking_data,
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_book, on_success, on_error)
        self.thread_pool.start(task)

    def get_my_bookings_async(self, on_success, on_error):
        """Récupérer l'historique des réservations (async, non-bloquant)"""
        async def _get_bookings():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/my-bookings",
                    # Pas besoin de param user_id, géré par le token JWT
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_get_bookings, on_success, on_error)
        self.thread_pool.start(task)
    
    def query_assistant_async(self, message: str, on_success, on_error):
        """Interroger l'assistant IA avec support de navigation (async, non-bloquant)"""
        async def _query():
            # Utiliser un nouveau client pour chaque thread/boucle pour éviter "Event loop is closed"
            # Timeout 130s pour correspondre à la config backend
            async with httpx.AsyncClient(timeout=130.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/assistant",
                    json={"message": message},
                    headers=self._get_headers()
                )
                return self._handle_response(response)
        
        task = ApiTask(_query, on_success, on_error)
        self.thread_pool.start(task)

    def get_autocomplete_async(self, keyword, on_success, on_error):
        """Obtenir des suggestions d'autocomplétion (async, non-bloquant)"""
        # Annuler les tâches précédentes serait bien, mais requiert une gestion complexe des tâches
        # Pour l'instant on compte sur le debounce du côté Vue
        async def _autocomplete():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/autocomplete",
                    params={"q": keyword},
                    headers=self._get_headers(),
                    timeout=5.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_autocomplete, on_success, on_error)
        self.thread_pool.start(task)
    
    def book_hotel_async(self, booking_data: dict, on_success, on_error):
        """Réserver un hôtel (async, non-bloquant)"""
        async def _book_hotel():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/travel/book/hotel",
                    json=booking_data,
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_book_hotel, on_success, on_error)
        self.thread_pool.start(task)
    
    def search_cities_async(self, keyword: str, on_success, on_error):
        """Rechercher des villes/aéroports (async, non-bloquant) - pour autocomplétion"""
        async def _search_cities():
            params = {"keyword": keyword}
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/cities/search",
                    params=params,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_search_cities, on_success, on_error)
        self.thread_pool.start(task)
    
    def consult_ai_async(self, mode: str, message: str, context: dict,
                         on_success, on_error):
        """
        Consulter l'assistant IA (async, non-bloquant).
        Utilise le client HTTP persistant pour de meilleures performances.
        
        Args:
            mode: Mode de consultation (compare, budget, policy, free)
            message: Message/question de l'utilisateur
            context: Dictionnaire de contexte (devrait contenir des dicts OfferDTO/BookingDTO)
            on_success: Callback pour une réponse réussie
            on_error: Callback pour les erreurs
        """
        async def _consult():
            # Utiliser un nouveau client avec timeout 130s pour gérer les réponses IA lentes
            async with httpx.AsyncClient(timeout=130.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/ai/consult",
                    json={
                        "mode": mode,
                        "message": message,
                        "context": context,  # Déjà formaté comme dict ConsultContext
                        "language": "fr",
                        "stream": False
                    },
                    headers=self._get_headers()
                )
                return self._handle_response(response)
        
        task = ApiTask(_consult, on_success, on_error)
        self.thread_pool.start(task)
    
    # ========================================================================
    # Gestion des Réponses
    # ========================================================================
    
    def _handle_response(self, response: httpx.Response):
        """Traite la réponse HTTP"""
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text}
        
        if response.status_code >= 400:
            msg = data.get("detail", "Erreur API")
            raise RuntimeError(msg)
        
        return data
