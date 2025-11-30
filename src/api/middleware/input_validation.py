"""Input validation middleware for BrainForge API."""

import re
from typing import Any
from urllib.parse import unquote

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive input validation and injection attack prevention."""

    def __init__(self, app):
        super().__init__(app)
        # Patterns for common injection attacks
        self.sql_injection_patterns = [
            r"(?i)(union\s+select|select\s+.*from|insert\s+into|drop\s+table|delete\s+from)",
            r"(?i)(--|\#|\/\*|\*\/)",
            r"(?i)(xp_cmdshell|exec\(|sp_|sys\.)",
        ]

        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
        ]

        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
        ]

        self.command_injection_patterns = [
            r"[;&|`]",
            r"\$\(.*\)",
            r"\|\|.*\|\|",
        ]

    async def dispatch(self, request: Request, call_next) -> Any:
        """Process request with input validation."""
        # Validate path parameters
        if request.url.path:
            self._validate_path(request.url.path)

        # Validate query parameters
        if request.url.query:
            self._validate_query_params(request.url.query)

        # Validate headers
        self._validate_headers(request.headers)

        # Process request
        response = await call_next(request)
        return response

    def _validate_path(self, path: str) -> None:
        """Validate URL path for path traversal and injection attempts."""
        decoded_path = unquote(path)

        # Check for path traversal
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, decoded_path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid path parameter detected"
                )

        # Check for injection attempts
        for pattern in self.sql_injection_patterns + self.xss_patterns:
            if re.search(pattern, decoded_path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malicious input detected in path"
                )

    def _validate_query_params(self, query: str) -> None:
        """Validate query parameters for injection attacks."""
        decoded_query = unquote(query)

        # Check for SQL injection
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, decoded_query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SQL injection attempt detected"
                )

        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, decoded_query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="XSS attempt detected"
                )

        # Check for command injection
        for pattern in self.command_injection_patterns:
            if re.search(pattern, decoded_query):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Command injection attempt detected"
                )

    def _validate_headers(self, headers) -> None:
        """Validate HTTP headers for injection attempts."""
        # Check User-Agent for suspicious patterns
        user_agent = headers.get("user-agent", "")
        if user_agent:
            for pattern in self.sql_injection_patterns + self.xss_patterns:
                if re.search(pattern, user_agent.lower()):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Suspicious User-Agent header detected"
                    )

        # Check Referer header
        referer = headers.get("referer", "")
        if referer:
            for pattern in self.sql_injection_patterns + self.xss_patterns:
                if re.search(pattern, referer.lower()):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Suspicious Referer header detected"
                    )


def create_input_validation_middleware(app) -> InputValidationMiddleware:
    """Create input validation middleware."""
    return InputValidationMiddleware(app)
