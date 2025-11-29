"""Base API client with retry logic and error handling for external APIs."""

import logging
import time
import asyncio
from typing import Any, Dict, Optional, Callable
from abc import ABC, abstractmethod

import aiohttp
from aiohttp import ClientSession, ClientError

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Base class for external API clients with built-in retry logic and error handling."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._session: Optional[ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    @abstractmethod
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        pass
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Use provided headers or get default headers
        request_headers = headers or await self._get_headers()
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=request_headers
                ) as response:
                    
                    if response.status == 200:
                        return await self._handle_success_response(response)
                    elif response.status == 429:  # Rate limit
                        await self._handle_rate_limit(response, attempt)
                    elif 400 <= response.status < 500:
                        return await self._handle_client_error(response, attempt)
                    elif response.status >= 500:
                        return await self._handle_server_error(response, attempt)
                    else:
                        return await self._handle_other_status(response, attempt)
                        
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout on attempt {attempt + 1} for {url}")
                if attempt == self.max_retries:
                    raise TimeoutError(f"Request timed out after {self.max_retries} attempts")
                
            except ClientError as e:
                logger.warning(f"Client error on attempt {attempt + 1} for {url}: {e}")
                if attempt == self.max_retries:
                    raise ConnectionError(f"Failed to connect after {self.max_retries} attempts: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                if attempt == self.max_retries:
                    raise
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise Exception(f"Failed to complete request after {self.max_retries} attempts")
    
    async def _handle_success_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle successful response."""
        try:
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                text = await response.text()
                return {"text": text, "status_code": response.status}
        except Exception as e:
            logger.error(f"Failed to parse successful response: {e}")
            return {"error": f"Failed to parse response: {e}", "status_code": response.status}
    
    async def _handle_rate_limit(self, response: aiohttp.ClientResponse, attempt: int) -> Dict[str, Any]:
        """Handle rate limit response."""
        retry_after = response.headers.get('retry-after', '1')
        try:
            wait_time = float(retry_after)
        except ValueError:
            wait_time = 1.0
        
        logger.warning(f"Rate limited. Retry after {wait_time}s (attempt {attempt + 1})")
        
        if attempt < self.max_retries:
            await asyncio.sleep(wait_time)
            # This will trigger a retry in the main loop
            raise ConnectionError("Rate limit encountered - retrying")
        else:
            return {
                "error": "Rate limit exceeded",
                "status_code": 429,
                "retry_after": wait_time
            }
    
    async def _handle_client_error(self, response: aiohttp.ClientResponse, attempt: int) -> Dict[str, Any]:
        """Handle client error responses (4xx)."""
        error_data = await self._parse_error_response(response)
        logger.error(f"Client error (attempt {attempt + 1}): {error_data}")
        
        # Don't retry on client errors (except 429 which is handled separately)
        return {
            "error": "Client error",
            "status_code": response.status,
            "details": error_data
        }
    
    async def _handle_server_error(self, response: aiohttp.ClientResponse, attempt: int) -> Dict[str, Any]:
        """Handle server error responses (5xx)."""
        error_data = await self._parse_error_response(response)
        logger.warning(f"Server error (attempt {attempt + 1}): {error_data}")
        
        if attempt == self.max_retries:
            return {
                "error": "Server error",
                "status_code": response.status,
                "details": error_data
            }
        else:
            # This will trigger a retry in the main loop
            raise ConnectionError(f"Server error {response.status} - retrying")
    
    async def _handle_other_status(self, response: aiohttp.ClientResponse, attempt: int) -> Dict[str, Any]:
        """Handle other status codes."""
        error_data = await self._parse_error_response(response)
        logger.warning(f"Unexpected status {response.status} (attempt {attempt + 1}): {error_data}")
        
        return {
            "error": f"Unexpected status {response.status}",
            "status_code": response.status,
            "details": error_data
        }
    
    async def _parse_error_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Parse error response body."""
        try:
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                text = await response.text()
                return {"text": text}
        except Exception as e:
            return {"parse_error": str(e)}
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request('GET', endpoint, params=params)
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                  json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request('POST', endpoint, data=data, json_data=json_data)
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None,
                 json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request('PUT', endpoint, data=data, json_data=json_data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request('DELETE', endpoint)
    
    def set_api_key(self, api_key: str):
        """Update the API key."""
        self.api_key = api_key
    
    def set_retry_config(self, max_retries: int, retry_delay: float):
        """Update retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def health_check(self) -> bool:
        """Perform a health check on the API."""
        try:
            response = await self.get('/health')  # Common health check endpoint
            return response.get('status') == 'ok' or 'healthy' in str(response).lower()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information if available."""
        # This would typically check headers from the last response
        # For now, return basic info
        return {
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout
        }


class ResilientAPIClient(BaseAPIClient):
    """Enhanced API client with additional resilience features."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
        circuit_breaker: Optional[Any] = None  # Would integrate with circuit breaker pattern
    ):
        super().__init__(base_url, api_key, max_retries, retry_delay, timeout)
        self.circuit_breaker = circuit_breaker
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0
    
    async def _make_request(self, *args, **kwargs) -> Dict[str, Any]:
        """Make request with circuit breaker integration."""
        
        # Check circuit breaker if available
        if self.circuit_breaker and self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is open - request blocked")
            return {
                "error": "Circuit breaker open - service unavailable",
                "circuit_breaker_state": "open"
            }
        
        self.request_count += 1
        
        try:
            result = await super()._make_request(*args, **kwargs)
            
            if 'error' not in result or result.get('status_code', 500) < 400:
                self.success_count += 1
                # Notify circuit breaker of success
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
            else:
                self.error_count += 1
                # Notify circuit breaker of failure
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
            
            return result
            
        except Exception as e:
            self.error_count += 1
            # Notify circuit breaker of failure
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get request statistics."""
        total_requests = self.request_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "circuit_breaker_state": self.circuit_breaker.state if self.circuit_breaker else "not_configured"
        }
    
    def reset_stats(self):
        """Reset request statistics."""
        self.request_count = 0
        self.error_count = 0
        self.success_count = 0