"""
Async API Client for Desktop App
Uses httpx for async HTTP requests to prevent UI freezing.
"""

import httpx
from typing import Optional
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class ApiTaskSignals(QObject):
    """
    Signals for ApiTask to communicate with main thread.
    Qt signals are thread-safe and automatically queued to the main thread.
    """
    finished = Signal(object)  # Emits result data
    error = Signal(Exception)  # Emits exception


class ApiTask(QRunnable):
    """
    Runnable task for async API calls.
    Executes in background thread to prevent UI freezing.
    Uses signals for thread-safe callbacks.
    """
    
    def __init__(self, func, callback, error_callback):
        super().__init__()
        self.func = func
        self.signals = ApiTaskSignals()
        self.setAutoDelete(False)  # Prevent deletion before signal delivery
        
        # Connect signals to callbacks with QueuedConnection for thread safety
        from PySide6.QtCore import Qt
        if callback:
            self.signals.finished.connect(callback, Qt.QueuedConnection)
        if error_callback:
            self.signals.error.connect(error_callback, Qt.QueuedConnection)
    
    def run(self):
        """Execute the async function in background thread"""
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.func())
            loop.close()
            
            # Emit result via signal (thread-safe!)
            self.signals.finished.emit(result)
        except Exception as e:
            # Emit error via signal (thread-safe!)
            self.signals.error.emit(e)


class AsyncApiClient(QObject):
    """
    Async API client that doesn't freeze the UI.
    Uses QThreadPool to run async operations in background.
    """
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.thread_pool = QThreadPool()
        self.token = None  # Will be set after login
        self._http_client: Optional[httpx.AsyncClient] = None  # Persistent client
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create persistent HTTP client (lazy init)"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(35.0))
        return self._http_client
    
    async def close(self):
        """Close HTTP client - call on app shutdown"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    def _get_headers(self) -> dict:
        """Get headers with authentication if token is set"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    # ========================================================================
    # Async API Methods
    # ========================================================================
    
    def register_async(self, username: str, email: str, password: str, 
                      on_success, on_error):
        """Register user (async, non-blocking)"""
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
        """Login user (async, non-blocking)"""
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
                           budget: Optional[int], on_success, on_error):
        """Search travel offers (async, non-blocking)"""
        async def _search():
            params = {
                "departure": departure,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
            }
            if budget is not None:
                params["budget"] = budget
            
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
        """Get travel offer details (async, non-blocking)"""
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

    def get_packages_async(self, departure: str, destination: str, 
                          depart_date: str, return_date: Optional[str],
                          on_success, on_error):
        """Get packages (async, non-blocking)"""
        async def _get_packages():
            params = {
                "departure": departure,
                "destination": destination,
                "depart_date": depart_date,
            }
            if return_date:
                params["return_date"] = return_date
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/packages",
                    params=params,
                    headers=self._get_headers(),
                    timeout=20.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_get_packages, on_success, on_error)
        self.thread_pool.start(task)

    def get_hotels_async(self, city_code: str, on_success, on_error):
        """Get hotels (async, non-blocking)"""
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
        """Book a flight (async, non-blocking)"""
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
        """Get user's booking history (async, non-blocking)"""
        async def _get_bookings():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/travel/my-bookings",
                    # No user_id param needed, handled by JWT in headers
                    headers=self._get_headers(),
                    timeout=15.0
                )
                return self._handle_response(response)
        
        task = ApiTask(_get_bookings, on_success, on_error)
        self.thread_pool.start(task)

    def get_autocomplete_async(self, keyword, on_success, on_error):
        """Get autocomplete suggestions (async, non-blocking)"""
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
        """Book a hotel (async, non-blocking)"""
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
        """Search for cities/airports (async, non-blocking) - for autocomplete"""
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
        Consult AI assistant (async, non-blocking).
        Uses persistent HTTP client for better performance.
        
        Args:
            mode: Consultation mode (compare, budget, policy, free)
            message: User's message/question
            context: Context dict (should contain OfferDTO/BookingDTO dicts)
            on_success: Callback for successful response
            on_error: Callback for errors
        """
        async def _consult():
            client = await self._get_http_client()  # Persistent client
            response = await client.post(
                f"{self.base_url}/api/ai/consult",
                json={
                    "mode": mode,
                    "message": message,
                    "context": context,  # Already formatted as ConsultContext dict
                    "language": "fr",
                    "stream": False
                },
                headers=self._get_headers()
            )
            return self._handle_response(response)
        
        task = ApiTask(_consult, on_success, on_error)
        self.thread_pool.start(task)
    
    # ========================================================================
    # Response Handling
    # ========================================================================
    
    def _handle_response(self, response: httpx.Response):
        """Handle HTTP response"""
        try:
            data = response.json()
        except Exception:
            data = {"detail": response.text}
        
        if response.status_code >= 400:
            msg = data.get("detail", "Erreur API")
            raise RuntimeError(msg)
        
        return data
