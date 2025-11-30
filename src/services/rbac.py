"""Role-Based Access Control (RBAC) service for BrainForge."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.orm.user import User
from src.models.role import (
    Permission,
    PermissionCheck,
    PermissionResponse,
    UserRole,
    UserRoleCreate,
    UserRoleResponse,
    get_permissions_for_role,
    has_permission,
)
from src.services.sqlalchemy_service import SQLAlchemyService

logger = logging.getLogger(__name__)


class RBACService(SQLAlchemyService[UserRoleResponse]):
    """Service for managing role-based access control."""
    
    def __init__(self):
        super().__init__(UserRoleResponse)
    
    async def assign_role(
        self,
        db: AsyncSession,
        user_id: UUID,
        role: UserRole,
        granted_by: UUID
    ) -> UserRoleResponse:
        """Assign a role to a user.
        
        Args:
            db: Database session
            user_id: User ID to assign role to
            role: Role to assign
            granted_by: User ID of the grantor
            
        Returns:
            User role assignment
        """
        # Check if user exists
        user = await db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if grantor exists
        grantor = await db.get(User, granted_by)
        if not grantor:
            raise ValueError(f"Grantor with ID {granted_by} not found")
        
        # Create role assignment
        role_create = UserRoleCreate(
            user_id=user_id,
            role=role,
            granted_by=granted_by
        )
        
        return await self.create(db, role_create)
    
    async def get_user_roles(self, db: AsyncSession, user_id: UUID) -> list[UserRole]:
        """Get all roles assigned to a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of user roles
        """
        # In a real implementation, this would query a user_roles table
        # For now, return default role based on user status
        user = await db.get(User, user_id)
        if not user:
            return []
        
        # Default role assignment logic
        if user.username == "admin":
            return [UserRole.ADMIN]
        elif user.is_active:
            return [UserRole.USER]
        else:
            return [UserRole.GUEST]
    
    async def check_permission(
        self,
        db: AsyncSession,
        permission_check: PermissionCheck
    ) -> PermissionResponse:
        """Check if a user has a specific permission.
        
        Args:
            db: Database session
            permission_check: Permission check request
            
        Returns:
            Permission check response
        """
        user_roles = await self.get_user_roles(db, permission_check.user_id)
        
        if not user_roles:
            return PermissionResponse(
                has_permission=False,
                reason="User has no roles assigned"
            )
        
        # Check each role for the permission
        for role in user_roles:
            if has_permission(role, permission_check.permission):
                return PermissionResponse(has_permission=True)
        
        return PermissionResponse(
            has_permission=False,
            reason=f"User roles {user_roles} do not have permission {permission_check.permission}"
        )
    
    async def get_user_permissions(self, db: AsyncSession, user_id: UUID) -> list[Permission]:
        """Get all permissions for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of user permissions
        """
        user_roles = await self.get_user_roles(db, user_id)
        permissions = set()
        
        for role in user_roles:
            permissions.update(get_permissions_for_role(role))
        
        return list(permissions)
    
    async def can_access_resource(
        self,
        db: AsyncSession,
        user_id: UUID,
        resource_type: str,
        action: str,
        resource_id: UUID | None = None
    ) -> bool:
        """Check if user can access a specific resource.
        
        Args:
            db: Database session
            user_id: User ID
            resource_type: Type of resource (note, user, etc.)
            action: Action to perform (read, write, delete)
            resource_id: Specific resource ID (optional)
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Map resource type and action to permission
        permission_map = {
            ("user", "create"): Permission.USER_CREATE,
            ("user", "read"): Permission.USER_READ,
            ("user", "update"): Permission.USER_UPDATE,
            ("user", "delete"): Permission.USER_DELETE,
            ("note", "create"): Permission.NOTE_CREATE,
            ("note", "read"): Permission.NOTE_READ,
            ("note", "update"): Permission.NOTE_UPDATE,
            ("note", "delete"): Permission.NOTE_DELETE,
            ("search", "execute"): Permission.SEARCH_EXECUTE,
            ("search", "history"): Permission.SEARCH_HISTORY,
            ("agent", "execute"): Permission.AGENT_EXECUTE,
            ("agent", "manage"): Permission.AGENT_MANAGE,
            ("ingestion", "create"): Permission.INGESTION_CREATE,
            ("ingestion", "read"): Permission.INGESTION_READ,
            ("ingestion", "delete"): Permission.INGESTION_DELETE,
            ("research", "execute"): Permission.RESEARCH_EXECUTE,
            ("research", "manage"): Permission.RESEARCH_MANAGE,
            ("quality", "assess"): Permission.QUALITY_ASSESS,
            ("quality", "review"): Permission.QUALITY_REVIEW,
            ("system", "monitor"): Permission.SYSTEM_MONITOR,
            ("system", "config"): Permission.SYSTEM_CONFIG,
            ("system", "backup"): Permission.SYSTEM_BACKUP,
        }
        
        permission = permission_map.get((resource_type, action))
        if not permission:
            logger.warning(f"Unknown permission for resource_type={resource_type}, action={action}")
            return False
        
        check = PermissionCheck(
            user_id=user_id,
            permission=permission,
            resource_id=resource_id
        )
        
        result = await self.check_permission(db, check)
        return result.has_permission


class PermissionMiddleware:
    """Middleware for enforcing RBAC permissions on API endpoints."""
    
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service
    
    async def enforce_permission(
        self,
        db: AsyncSession,
        user_id: UUID,
        endpoint: str,
        method: str,
        resource_id: UUID | None = None
    ) -> bool:
        """Enforce permission for API endpoint access.
        
        Args:
            db: Database session
            user_id: User ID
            endpoint: API endpoint path
            method: HTTP method
            resource_id: Resource ID if applicable
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Map endpoints to resource types and actions
        endpoint_permissions = self._map_endpoint_to_permission(endpoint, method)
        
        if not endpoint_permissions:
            logger.warning(f"No permission mapping for endpoint={endpoint}, method={method}")
            return True  # Allow access if no specific permission required
        
        resource_type, action = endpoint_permissions
        
        return await self.rbac_service.can_access_resource(
            db, user_id, resource_type, action, resource_id
        )
    
    def _map_endpoint_to_permission(self, endpoint: str, method: str) -> tuple[str, str] | None:
        """Map API endpoint to resource type and action.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            
        Returns:
            Tuple of (resource_type, action) or None if no mapping
        """
        endpoint_mappings = {
            # User endpoints
            ("/api/v1/auth/register", "POST"): ("user", "create"),
            ("/api/v1/auth/me", "GET"): ("user", "read"),
            ("/api/v1/users", "GET"): ("user", "read"),
            ("/api/v1/users/{user_id}", "GET"): ("user", "read"),
            ("/api/v1/users/{user_id}", "PUT"): ("user", "update"),
            ("/api/v1/users/{user_id}", "DELETE"): ("user", "delete"),
            
            # Note endpoints
            ("/api/v1/notes", "GET"): ("note", "read"),
            ("/api/v1/notes", "POST"): ("note", "create"),
            ("/api/v1/notes/{note_id}", "GET"): ("note", "read"),
            ("/api/v1/notes/{note_id}", "PUT"): ("note", "update"),
            ("/api/v1/notes/{note_id}", "DELETE"): ("note", "delete"),
            
            # Search endpoints
            ("/api/v1/search", "POST"): ("search", "execute"),
            ("/api/v1/search/history", "GET"): ("search", "history"),
            
            # Agent endpoints
            ("/api/v1/agent", "POST"): ("agent", "execute"),
            ("/api/v1/agent/{agent_id}", "GET"): ("agent", "manage"),
            ("/api/v1/agent/{agent_id}", "DELETE"): ("agent", "manage"),
            
            # Ingestion endpoints
            ("/api/v1/ingestion/pdf", "POST"): ("ingestion", "create"),
            ("/api/v1/ingestion", "GET"): ("ingestion", "read"),
            ("/api/v1/ingestion/{ingestion_id}", "DELETE"): ("ingestion", "delete"),
            
            # Research endpoints
            ("/api/v1/research", "POST"): ("research", "execute"),
            ("/api/v1/research/{research_id}", "GET"): ("research", "manage"),
            ("/api/v1/research/{research_id}", "DELETE"): ("research", "manage"),
            
            # Quality endpoints
            ("/api/v1/quality/assess", "POST"): ("quality", "assess"),
            ("/api/v1/quality/review", "GET"): ("quality", "review"),
            
            # System endpoints
            ("/api/v1/system/health", "GET"): ("system", "monitor"),
            ("/api/v1/system/config", "GET"): ("system", "config"),
            ("/api/v1/system/backup", "POST"): ("system", "backup"),
        }
        
        # Try exact match first
        key = (endpoint, method)
        if key in endpoint_mappings:
            return endpoint_mappings[key]
        
        # Try pattern matching for path parameters
        for (pattern_endpoint, pattern_method), permission in endpoint_mappings.items():
            if pattern_method == method and self._endpoint_matches_pattern(endpoint, pattern_endpoint):
                return permission
        
        return None
    
    def _endpoint_matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches a pattern with path parameters.
        
        Args:
            endpoint: Actual endpoint path
            pattern: Pattern with {param} placeholders
            
        Returns:
            True if endpoint matches pattern
        """
        endpoint_parts = endpoint.strip("/").split("/")
        pattern_parts = pattern.strip("/").split("/")
        
        if len(endpoint_parts) != len(pattern_parts):
            return False
        
        for endpoint_part, pattern_part in zip(endpoint_parts, pattern_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Path parameter matches any value
            if endpoint_part != pattern_part:
                return False
        
        return True


# Global RBAC service instance
rbac_service = RBACService()
permission_middleware = PermissionMiddleware(rbac_service)


def get_rbac_service() -> RBACService:
    """Get RBAC service dependency."""
    return rbac_service


def get_permission_middleware() -> PermissionMiddleware:
    """Get permission middleware dependency."""
    return permission_middleware