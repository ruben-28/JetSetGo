"""
Base Gateway Module
Provides abstract base class for all external API gateways with:
- Async HTTP client (httpx)
- Configuration management (environment variables)
- Retry logic with exponential backoff
- Custom exception handling
- Mock mode detection
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
from asyncio import sleep


# ============================================================================
# Custom Exceptions
# ============================================================================

class GatewayError(Exception):
    """Base exception for all gateway errors"""
    pass


class GatewayConfigError(GatewayError):
    """Raised when gateway configuration is invalid or missing"""
    pass


class GatewayTimeoutError(GatewayError):
    """Raised when gateway request times out"""
    pass


class GatewayAPIError(GatewayError):
    """Raised when external API returns an error"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ============================================================================
# Base Gateway
# ============================================================================

class BaseGateway(ABC):
    """
    Abstract base class for all API gateways.
    
    Responsibilities:
    - Manage httpx.AsyncClient lifecycle
    - Load configuration from environment variables
    - Implement retry logic with exponential backoff
    - Provide mock mode detection
    - Handle common HTTP errors
    
    Subclasses must implement:
    - _get_required_config_keys(): List of required env var keys
    """
    
    def __init__(self):
        """Initialize gateway with configuration and HTTP client"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._client: Optional[httpx.AsyncClient] = None
        self._config = self._load_config()
        self._is_mock = self._detect_mock_mode()
        
        if self._is_mock:
            self.logger.warning(f"{self.__class__.__name__} running in MOCK MODE (missing API keys)")
    
    # ========================================================================
    # Configuration Management
    # ========================================================================
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            "timeout": int(os.getenv("GATEWAY_TIMEOUT", "30")),
            "max_retries": int(os.getenv("GATEWAY_MAX_RETRIES", "3")),
            "retry_delay": float(os.getenv("GATEWAY_RETRY_DELAY", "1.0")),
        }
        
        # Load gateway-specific config
        for key in self._get_required_config_keys():
            config[key] = os.getenv(key)
        
        return config
    
    @abstractmethod
    def _get_required_config_keys(self) -> list[str]:
        """
        Return list of required environment variable keys.
        Subclasses must implement this.
        
        Example:
            return ["TRAVEL_API_KEY", "TRAVEL_API_BASE_URL"]
        """
        pass
    
    def _get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)
    
    def _detect_mock_mode(self) -> bool:
        """
        Detect if gateway should run in mock mode.
        Returns True if any required API key is missing.
        """
        required_keys = self._get_required_config_keys()
        for key in required_keys:
            if not self._config.get(key):
                return True
        return False
    
    def is_mock_mode(self) -> bool:
        """Check if gateway is running in mock mode"""
        return self._is_mock
    
    # ========================================================================
    # HTTP Client Management (with proper cleanup)
    # ========================================================================
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            timeout = httpx.Timeout(self._config["timeout"])
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client
    
    async def close(self):
        """Close HTTP client (cleanup) - IMPORTANT: Call this to prevent resource leaks"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - automatically closes client"""
        await self.close()
        return False

    
    # ========================================================================
    # HTTP Request Methods
    # ========================================================================
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request
        
        Returns:
            Response JSON as dict
        
        Raises:
            GatewayTimeoutError: On timeout
            GatewayAPIError: On API error response
            GatewayError: On other errors
        """
        client = await self._get_client()
        
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        
        except httpx.TimeoutException as e:
            self.logger.error(f"Request timeout: {url}")
            raise GatewayTimeoutError(f"Request timed out: {url}") from e
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error {e.response.status_code}: {url}")
            raise GatewayAPIError(
                f"API returned error: {e.response.status_code}",
                status_code=e.response.status_code
            ) from e
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise GatewayError(f"Request failed: {str(e)}") from e
    
    async def _retry_request(
        self,
        request_func,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute request with retry logic (exponential backoff).
        
        Args:
            request_func: Async function that makes the request
            max_retries: Max retry attempts (uses config default if None)
        
        Returns:
            Response JSON as dict
        
        Raises:
            GatewayError: After all retries exhausted
        """
        max_retries = max_retries or self._config["max_retries"]
        retry_delay = self._config["retry_delay"]
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await request_func()
            
            except GatewayTimeoutError as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                    await sleep(wait_time)
                else:
                    self.logger.error(f"All retries exhausted")
            
            except GatewayAPIError as e:
                # Don't retry on 4xx errors (client errors)
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                
                last_exception = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                    await sleep(wait_time)
                else:
                    self.logger.error(f"All retries exhausted")
        
        # All retries exhausted
        raise last_exception or GatewayError("Request failed after retries")
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def __repr__(self) -> str:
        mode = "MOCK" if self._is_mock else "LIVE"
        return f"<{self.__class__.__name__} mode={mode}>"
