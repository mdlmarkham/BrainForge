"""BrainForge AI Knowledge Base - FastAPI main application."""

import asyncio
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.compliance.constitution import ComplianceMiddleware, create_compliance_exception_handler

from .routes import agent, ingestion, notes, search, vault, obsidian, research, quality, auth


class MultipartSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for multipart/form-data boundary validation and request size limits."""

    def __init__(self, app, max_request_size: int = 100 * 1024 * 1024, max_multipart_body_size: int = 50 * 1024 * 1024):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.max_multipart_body_size = max_multipart_body_size

    async def dispatch(self, request: Request, call_next):
        # Check content type for multipart requests
        content_type = request.headers.get("content-type", "")

        if content_type.startswith("multipart/form-data"):
            # Validate boundary parameter
            if "boundary=" not in content_type:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid multipart request: missing boundary parameter"}
                )

            # Extract boundary
            boundary_part = content_type.split("boundary=")[1]
            boundary = boundary_part.split(";")[0].strip()

            # Validate boundary length and format
            if len(boundary) > 70:  # RFC 2046 limit
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid multipart request: boundary too long"}
                )

            # Check for boundary deformation attempts
            if any(char in boundary for char in ['\r', '\n', '"', "'"]):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid multipart request: boundary contains invalid characters"}
                )

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Request too large. Maximum size: {self.max_request_size} bytes"}
                    )
            except ValueError:
                pass

        response = await call_next(request)
        return response


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware for request timeout protection."""

    def __init__(self, app, timeout_seconds: int = 30):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next):
        try:
            # Use asyncio.wait_for to enforce timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
        except TimeoutError:
            return JSONResponse(
                status_code=408,
                content={"detail": f"Request timeout. Maximum allowed: {self.timeout_seconds} seconds"}
            )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="BrainForge AI Knowledge Base",
        description="AI-powered personal knowledge management system with constitutional compliance",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        max_request_size=100 * 1024 * 1024,  # 100MB limit
    )

    # Add compliance middleware
    app.add_middleware(ComplianceMiddleware)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add compliance exception handler
    app.add_exception_handler(Exception, create_compliance_exception_handler())

    # Include routers
    app.include_router(notes.router, prefix="/api/v1", tags=["Notes"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(agent.router, prefix="/api/v1", tags=["Agent"])
    app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])
    app.include_router(vault.router, prefix="/api/v1", tags=["Vault"])
    app.include_router(obsidian.router, prefix="/api/v1", tags=["Obsidian"])
    app.include_router(research.router, prefix="/api/v1", tags=["Research"])
    app.include_router(quality.router, prefix="/api/v1", tags=["Quality"])
    app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        return {"status": "healthy", "service": "brainforge"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "BrainForge AI Knowledge Base API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
