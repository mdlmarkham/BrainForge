"""Rate limiting middleware for BrainForge API."""

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""

    def __init__(
        self,
        app,
        default_limit: int = 100,
        window_seconds: int = 60,
        endpoint_limits: dict[str, int] | None = None
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.endpoint_limits = endpoint_limits or {}
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Any:
        """Process request with rate limiting."""
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path

        # Get rate limit for this endpoint
        limit = self.endpoint_limits.get(endpoint, self.default_limit)

        # Clean old requests
        current_time = time.time()
        self._clean_old_requests(client_ip, endpoint, current_time)

        # Check if rate limit exceeded
        if len(self.request_counts[(client_ip, endpoint)]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUENTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per {self.window_seconds} seconds.",
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Record this request
        self.request_counts[(client_ip, endpoint)].append(current_time)

        # Process request
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Try to get IP from X-Forwarded-For header (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _clean_old_requests(self, client_ip: str, endpoint: str, current_time: float) -> None:
        """Remove requests older than the time window."""
        key = (client_ip, endpoint)
        if key in self.request_counts:
            # Keep only requests within the time window
            self.request_counts[key] = [
                timestamp for timestamp in self.request_counts[key]
                if current_time - timestamp < self.window_seconds
            ]


# Default rate limits for different endpoint types
DEFAULT_ENDPOINT_LIMITS = {
    # Authentication endpoints - lower limits to prevent brute force
    "/api/v1/auth/login": 10,      # 10 requests per minute
    "/api/v1/auth/register": 5,    # 5 requests per minute

    # File upload endpoints - lower limits to prevent resource exhaustion
    "/api/v1/ingestion/pdf": 5,    # 5 requests per minute
    "/api/v1/ingestion/pdf/batch": 2,  # 2 requests per minute

    # Search endpoints - moderate limits
    "/api/v1/search": 30,          # 30 requests per minute

    # Default for all other endpoints
    "*": 100                       # 100 requests per minute
}


def create_rate_limit_middleware(app) -> RateLimitMiddleware:
    """Create rate limiting middleware with sensible defaults."""
    return RateLimitMiddleware(
        app,
        default_limit=100,
        window_seconds=60,
        endpoint_limits=DEFAULT_ENDPOINT_LIMITS
    )
