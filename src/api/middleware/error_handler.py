"""Error handling middleware for sanitizing error responses."""

import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for sanitizing error responses and preventing information disclosure."""

    def __init__(self, app, debug_mode: bool = False):
        super().__init__(app)
        self.debug_mode = debug_mode

    async def dispatch(self, request: Request, call_next) -> Any:
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response

        except HTTPException:
            # Re-raise HTTP exceptions as they are intentional
            raise

        except Exception as exc:
            # Log the full error for debugging
            logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}")
            if self.debug_mode:
                logger.debug(f"Full traceback: {traceback.format_exc()}")

            # Return sanitized error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later."
                }
            )


def create_error_handler_middleware(app, debug_mode: bool = False) -> ErrorHandlerMiddleware:
    """Create error handler middleware."""
    return ErrorHandlerMiddleware(app, debug_mode=debug_mode)
