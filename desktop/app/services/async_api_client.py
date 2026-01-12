"""
Async API Client for Desktop App
Uses httpx for async HTTP requests to prevent UI freezing.
"""

import httpx
from typing import Optional
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool


class ApiTask(QRunnable):
    """
    Runnable task for async API calls.
    Executes in background thread to prevent UI freezing.
    """
    
    def __init__(self, func, callback, error_callback):
        super().__init__()
        self.func = func
        self.callback = callback
        self.error_callback = error_callback
    
    def run(self):
        """Execute the async function in background thread"""
        import asyncio
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.func())
            loop.close()
            
            # Call success callback
            if self.callback:
                self.callback(result)
        except Exception as e:
            # Call error callback
            if self.error_callback:
                self.error_callback(e)


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
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
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
