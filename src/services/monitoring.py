"""Comprehensive monitoring and observability service for BrainForge."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.models.orm.user import User
from src.services.metrics.research_metrics import ResearchMetricsCollector

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Structured logging with JSON format for production monitoring."""
    
    def __init__(self, service_name: str = "brainforge"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
    
    def log_request(self, request: Request, user_id: Optional[UUID] = None, duration_ms: float = 0.0):
        """Log HTTP request with structured data.
        
        Args:
            request: FastAPI request object
            user_id: User ID if authenticated
            duration_ms: Request duration in milliseconds
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": self.service_name,
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "user_agent": request.headers.get("user-agent", ""),
            "ip_address": self._get_client_ip(request),
            "user_id": str(user_id) if user_id else None,
            "duration_ms": round(duration_ms, 2),
            "status_code": 200,  # Will be updated by response middleware
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_response(self, request: Request, status_code: int, user_id: Optional[UUID] = None):
        """Log HTTP response with structured data.
        
        Args:
            request: FastAPI request object
            status_code: HTTP status code
            user_id: User ID if authenticated
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": self.service_name,
            "event": "http_response",
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "user_id": str(user_id) if user_id else None,
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error: Exception, request: Optional[Request] = None, user_id: Optional[UUID] = None):
        """Log error with structured data.
        
        Args:
            error: Exception that occurred
            request: FastAPI request object (optional)
            user_id: User ID if authenticated
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "service": self.service_name,
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": str(user_id) if user_id else None,
        }
        
        if request:
            log_data.update({
                "method": request.method,
                "path": request.url.path,
            })
        
        self.logger.error(json.dumps(log_data))
    
    def log_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, Any]] = None):
        """Log metric with structured data.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Additional tags for the metric
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": self.service_name,
            "event": "metric",
            "metric_name": metric_name,
            "value": value,
        }
        
        if tags:
            log_data.update(tags)
        
        self.logger.info(json.dumps(log_data))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class MonitoringMiddleware:
    """Middleware for comprehensive request monitoring."""
    
    def __init__(self, structured_logger: StructuredLogger):
        self.structured_logger = structured_logger
    
    async def process_request(self, request: Request, user_id: Optional[UUID] = None):
        """Process incoming request for monitoring.
        
        Args:
            request: FastAPI request object
            user_id: User ID if authenticated
        """
        # Store start time for duration calculation
        request.state.start_time = time.time()
        request.state.user_id = user_id
        
        self.structured_logger.log_request(request, user_id)
    
    async def process_response(self, request: Request, response):
        """Process outgoing response for monitoring.
        
        Args:
            request: FastAPI request object
            response: FastAPI response object
        """
        duration_ms = (time.time() - request.state.start_time) * 1000
        user_id = getattr(request.state, 'user_id', None)
        
        # Update request log with duration
        self.structured_logger.log_request(request, user_id, duration_ms)
        self.structured_logger.log_response(request, response.status_code, user_id)
        
        # Log performance metric
        self.structured_logger.log_metric(
            "request_duration_ms",
            duration_ms,
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            }
        )
        
        return response


class HealthCheckService:
    """Service for health checks and system monitoring."""
    
    def __init__(self, db_config, metrics_collector: ResearchMetricsCollector):
        self.db_config = db_config
        self.metrics_collector = metrics_collector
    
    async def check_database_health(self, db: AsyncSession) -> Dict[str, Any]:
        """Check database health and connectivity.
        
        Args:
            db: Database session
            
        Returns:
            Database health status
        """
        try:
            # Test database connection with a simple query
            start_time = time.time()
            result = await db.execute(text("SELECT 1"))
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def check_system_health(self, db: AsyncSession) -> Dict[str, Any]:
        """Comprehensive system health check.
        
        Args:
            db: Database session
            
        Returns:
            System health status
        """
        health_checks = {}
        
        # Database health
        health_checks["database"] = await self.check_database_health(db)
        
        # Service health (placeholder for additional services)
        health_checks["api"] = {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        # Overall status
        all_healthy = all(check["status"] == "healthy" for check in health_checks.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": health_checks,
        }
    
    async def get_system_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive system metrics.
        
        Args:
            db: Database session
            
        Returns:
            System metrics
        """
        metrics = {}
        
        # Research metrics
        try:
            research_metrics = await self.metrics_collector.collect_aggregate_metrics(
                db, timedelta(hours=24)
            )
            metrics["research"] = research_metrics
        except Exception as e:
            metrics["research"] = {"error": str(e)}
        
        # System metrics
        metrics["system"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": self._get_uptime(),
        }
        
        return metrics
    
    def _get_uptime(self) -> int:
        """Get system uptime in seconds (placeholder implementation).
        
        Returns:
            Uptime in seconds
        """
        # In production, this would read from system metrics
        return int(time.time() - 3600)  # Placeholder: 1 hour uptime


class PerformanceMonitor:
    """Performance monitoring for critical operations."""
    
    def __init__(self, structured_logger: StructuredLogger):
        self.structured_logger = structured_logger
    
    async def monitor_operation(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """Context manager for monitoring operation performance.
        
        Args:
            operation_name: Name of the operation
            tags: Additional tags for the operation
            
        Returns:
            Context manager for performance monitoring
        """
        return PerformanceContext(self.structured_logger, operation_name, tags)


class PerformanceContext:
    """Context manager for performance monitoring."""
    
    def __init__(self, structured_logger: StructuredLogger, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        self.structured_logger = structured_logger
        self.operation_name = operation_name
        self.tags = tags or {}
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        self.structured_logger.log_metric(
            f"operation_{self.operation_name}_duration_ms",
            duration_ms,
            self.tags
        )
        
        if exc_type:
            self.structured_logger.log_error(exc_val, tags=self.tags)


# Global monitoring instances
structured_logger = StructuredLogger()
monitoring_middleware = MonitoringMiddleware(structured_logger)


def get_structured_logger() -> StructuredLogger:
    """Get structured logger dependency."""
    return structured_logger


def get_monitoring_middleware() -> MonitoringMiddleware:
    """Get monitoring middleware dependency."""
    return monitoring_middleware


def setup_structured_logging():
    """Setup structured logging configuration."""
    # Configure JSON formatter
    json_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add JSON handler
    handler = logging.StreamHandler()
    handler.setFormatter(json_formatter)
    root_logger.addHandler(handler)
    
    # Set log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO")
    root_logger.setLevel(getattr(logging, log_level.upper()))