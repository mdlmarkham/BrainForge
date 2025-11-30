"""Role-based access control models for BrainForge."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    
    ADMIN = "admin"           # Full system access
    USER = "user"             # Standard user access
    READ_ONLY = "read_only"   # Read-only access
    GUEST = "guest"           # Limited guest access


class Permission(str, Enum):
    """Individual permissions that can be assigned to roles."""
    
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Note management
    NOTE_CREATE = "note:create"
    NOTE_READ = "note:read"
    NOTE_UPDATE = "note:update"
    NOTE_DELETE = "note:delete"
    
    # Search operations
    SEARCH_EXECUTE = "search:execute"
    SEARCH_HISTORY = "search:history"
    
    # Agent operations
    AGENT_EXECUTE = "agent:execute"
    AGENT_MANAGE = "agent:manage"
    
    # Ingestion operations
    INGESTION_CREATE = "ingestion:create"
    INGESTION_READ = "ingestion:read"
    INGESTION_DELETE = "ingestion:delete"
    
    # Research operations
    RESEARCH_EXECUTE = "research:execute"
    RESEARCH_MANAGE = "research:manage"
    
    # Quality operations
    QUALITY_ASSESS = "quality:assess"
    QUALITY_REVIEW = "quality:review"
    
    # System operations
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"


class RolePermission(BaseModel):
    """Mapping of roles to permissions."""
    
    role: UserRole
    permissions: list[Permission]
    
    class Config:
        from_attributes = True


# Predefined role-permission mappings
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.NOTE_CREATE, Permission.NOTE_READ, Permission.NOTE_UPDATE, Permission.NOTE_DELETE,
        Permission.SEARCH_EXECUTE, Permission.SEARCH_HISTORY,
        Permission.AGENT_EXECUTE, Permission.AGENT_MANAGE,
        Permission.INGESTION_CREATE, Permission.INGESTION_READ, Permission.INGESTION_DELETE,
        Permission.RESEARCH_EXECUTE, Permission.RESEARCH_MANAGE,
        Permission.QUALITY_ASSESS, Permission.QUALITY_REVIEW,
        Permission.SYSTEM_MONITOR, Permission.SYSTEM_CONFIG, Permission.SYSTEM_BACKUP
    ],
    UserRole.USER: [
        Permission.USER_READ, Permission.USER_UPDATE,
        Permission.NOTE_CREATE, Permission.NOTE_READ, Permission.NOTE_UPDATE, Permission.NOTE_DELETE,
        Permission.SEARCH_EXECUTE, Permission.SEARCH_HISTORY,
        Permission.AGENT_EXECUTE,
        Permission.INGESTION_CREATE, Permission.INGESTION_READ,
        Permission.RESEARCH_EXECUTE,
        Permission.QUALITY_ASSESS
    ],
    UserRole.READ_ONLY: [
        Permission.USER_READ,
        Permission.NOTE_READ,
        Permission.SEARCH_EXECUTE,
        Permission.INGESTION_READ
    ],
    UserRole.GUEST: [
        Permission.NOTE_READ,
        Permission.SEARCH_EXECUTE
    ]
}


class UserRoleCreate(BaseModel):
    """Schema for creating user roles."""
    
    user_id: UUID
    role: UserRole
    granted_by: UUID = Field(description="User ID of the grantor")


class UserRoleResponse(BaseModel):
    """Schema for user role responses."""
    
    id: UUID
    user_id: UUID
    role: UserRole
    granted_by: UUID
    granted_at: str
    is_active: bool
    
    class Config:
        from_attributes = True


class PermissionCheck(BaseModel):
    """Schema for permission check requests."""
    
    user_id: UUID
    permission: Permission
    resource_id: UUID | None = None


class PermissionResponse(BaseModel):
    """Schema for permission check responses."""
    
    has_permission: bool
    reason: str | None = None


def get_permissions_for_role(role: UserRole) -> list[Permission]:
    """Get permissions for a specific role.
    
    Args:
        role: User role
        
    Returns:
        List of permissions for the role
    """
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission.
    
    Args:
        role: User role
        permission: Permission to check
        
    Returns:
        True if role has permission, False otherwise
    """
    return permission in get_permissions_for_role(role)


def get_highest_role(roles: list[UserRole]) -> UserRole:
    """Get the highest role from a list of roles (hierarchical ordering).
    
    Args:
        roles: List of user roles
        
    Returns:
        Highest role in the hierarchy
    """
    role_hierarchy = [UserRole.ADMIN, UserRole.USER, UserRole.READ_ONLY, UserRole.GUEST]
    
    for role in role_hierarchy:
        if role in roles:
            return role
    
    return UserRole.GUEST  # Default to lowest role