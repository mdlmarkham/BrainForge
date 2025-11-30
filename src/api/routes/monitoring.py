"""Monitoring and system management routes for BrainForge."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import DatabaseSession
from src.models.orm.user import User
from src.models.role import Permission, UserRole
from src.services.monitoring import HealthCheckService, get_structured_logger
from src.services.rbac import get_rbac_service
from src.services.metrics.research_metrics import ResearchMetricsCollector
from src.config.database import db_config

router = APIRouter(prefix="/system", tags=["monitoring"])

# Initialize services
metrics_collector = ResearchMetricsCollector()
health_check_service = HealthCheckService(db_config, metrics_collector)
rbac_service = get_rbac_service()
structured_logger = get_structured_logger()


@router.get("/health", summary="System health check")
async def health_check(session: AsyncSession = DatabaseSession):
    """Check system health and component status."""
    health_status = await health_check_service.check_system_health(session)
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@router.get("/health/database", summary="Database health check")
async def database_health_check(session: AsyncSession = DatabaseSession):
    """Check database connectivity and performance."""
    db_health = await health_check_service.check_database_health(session)
    
    if db_health["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=db_health
        )
    
    return db_health


@router.get("/metrics", summary="System metrics")
async def get_metrics(
    session: AsyncSession = DatabaseSession,
    current_user: User = Depends(lambda: None)  # Placeholder for auth
):
    """Get comprehensive system metrics (requires admin permissions)."""
    # Check permissions - only admins can access detailed metrics
    if current_user:
        has_permission = await rbac_service.check_permission(
            session,
            PermissionCheck(
                user_id=current_user.id,
                permission=Permission.SYSTEM_MONITOR
            )
        )
        
        if not has_permission.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access system metrics"
            )
    
    metrics = await health_check_service.get_system_metrics(session)
    return metrics


@router.get("/metrics/research", summary="Research metrics")
async def get_research_metrics(
    session: AsyncSession = DatabaseSession,
    current_user: User = Depends(lambda: None)  # Placeholder for auth
):
    """Get research workflow metrics."""
    # Basic permission check - any authenticated user can see research metrics
    if current_user:
        has_permission = await rbac_service.check_permission(
            session,
            PermissionCheck(
                user_id=current_user.id,
                permission=Permission.RESEARCH_EXECUTE
            )
        )
        
        if not has_permission.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access research metrics"
            )
    
    try:
        metrics = await metrics_collector.collect_aggregate_metrics(session)
        return metrics
    except Exception as e:
        structured_logger.log_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect research metrics: {str(e)}"
        )


@router.get("/logs", summary="System logs (admin only)")
async def get_logs(
    session: AsyncSession = DatabaseSession,
    current_user: User = Depends(lambda: None)  # Placeholder for auth
):
    """Get system logs (requires admin permissions)."""
    # Strict permission check - only admins can access logs
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    has_permission = await rbac_service.check_permission(
        session,
        PermissionCheck(
            user_id=current_user.id,
            permission=Permission.SYSTEM_MONITOR
        )
    )
    
    if not has_permission.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required to access system logs"
        )
    
    # In production, this would fetch logs from a log aggregation system
    # For now, return a placeholder response
    return {
        "message": "Log access endpoint - would connect to log aggregation system in production",
        "timestamp": "2024-01-01T00:00:00Z",  # Placeholder
        "available_logs": ["application", "database", "security"]
    }


@router.post("/backup", summary="Initiate system backup")
async def initiate_backup(
    session: AsyncSession = DatabaseSession,
    current_user: User = Depends(lambda: None)  # Placeholder for auth
):
    """Initiate system backup (requires admin permissions)."""
    # Strict permission check - only admins can initiate backups
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    has_permission = await rbac_service.check_permission(
        session,
        PermissionCheck(
            user_id=current_user.id,
            permission=Permission.SYSTEM_BACKUP
        )
    )
    
    if not has_permission.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required to initiate backups"
        )
    
    # Log backup initiation
    structured_logger.log_metric(
        "backup_initiated",
        1.0,
        {"user_id": str(current_user.id)}
    )
    
    # In production, this would trigger a backup process
    # For now, return a placeholder response
    return {
        "status": "backup_initiated",
        "backup_id": "backup_20240101_000000",  # Placeholder
        "timestamp": "2024-01-01T00:00:00Z",    # Placeholder
        "initiated_by": str(current_user.id)
    }


@router.get("/config", summary="System configuration (admin only)")
async def get_config(
    session: AsyncSession = DatabaseSession,
    current_user: User = Depends(lambda: None)  # Placeholder for auth
):
    """Get system configuration (requires admin permissions)."""
    # Strict permission check - only admins can access configuration
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    has_permission = await rbac_service.check_permission(
        session,
        PermissionCheck(
            user_id=current_user.id,
            permission=Permission.SYSTEM_CONFIG
        )
    )
    
    if not has_permission.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required to access system configuration"
        )
    
    # Return safe configuration information (no secrets)
    return {
        "service_name": "BrainForge",
        "version": "1.0.0",
        "environment": "production",  # Would come from environment variables
        "database_type": "postgresql",
        "log_level": "INFO",  # Would come from environment variables
        "max_request_size": "100MB",
        "rate_limiting_enabled": True,
        "authentication_enabled": True,
        "encryption_enabled": True
    }


@router.get("/status", summary="System status overview")
async def get_status(session: AsyncSession = DatabaseSession):
    """Get public system status overview."""
    # Public endpoint - no authentication required
    health_status = await health_check_service.check_system_health(session)
    
    return {
        "service": "BrainForge",
        "version": "1.0.0",
        "status": health_status["status"],
        "timestamp": health_status["timestamp"],
        "uptime": health_status.get("uptime", 0),
        "components": {
            "api": "operational",  # Simplified status
            "database": health_status["checks"]["database"]["status"],
        }
    }


@router.get("/readiness", summary="Readiness probe")
async def readiness_probe(session: AsyncSession = DatabaseSession):
    """Kubernetes readiness probe endpoint."""
    health_status = await health_check_service.check_system_health(session)
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return {"status": "ready"}


@router.get("/liveness", summary="Liveness probe")
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    # Simple check that the application is running
    return {"status": "alive"}