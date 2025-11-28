"""Base service layer interfaces for BrainForge."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar
from uuid import UUID

T = TypeVar('T')
CreateT = TypeVar('CreateT')
UpdateT = TypeVar('UpdateT')


class BaseService(ABC, Generic[T, CreateT, UpdateT]):
    """Base service interface for CRUD operations."""

    @abstractmethod
    async def create(self, data: CreateT) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get(self, id: UUID) -> T | None:
        """Get an entity by ID."""
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List entities with pagination."""
        pass

    @abstractmethod
    async def update(self, id: UUID, data: UpdateT) -> T | None:
        """Update an entity."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete an entity."""
        pass


class SearchService(ABC, Generic[T]):
    """Base service interface for search operations."""

    @abstractmethod
    async def search(self, query: str, filters: dict | None = None, limit: int = 50) -> list[T]:
        """Search entities with optional filters."""
        pass

    @abstractmethod
    async def hybrid_search(self, semantic_query: str, filters: dict | None = None, limit: int = 50) -> list[T]:
        """Perform hybrid search combining semantic and metadata filtering."""
        pass


class AuditService(ABC):
    """Base service interface for audit operations."""

    @abstractmethod
    async def log_operation(self, operation: str, entity_id: UUID, user: str, details: dict) -> None:
        """Log an operation for audit purposes."""
        pass

    @abstractmethod
    async def get_audit_trail(self, entity_id: UUID) -> list[dict]:
        """Get audit trail for an entity."""
        pass


class ValidationService(ABC):
    """Base service interface for validation operations."""

    @abstractmethod
    async def validate_input(self, data: dict, schema: dict) -> dict:
        """Validate input data against a schema."""
        pass

    @abstractmethod
    async def validate_ai_output(self, output: dict, expected_schema: dict) -> dict:
        """Validate AI-generated output against expected schema."""
        pass


class ErrorHandler(ABC):
    """Base error handling interface."""

    @abstractmethod
    async def handle_error(self, error: Exception, context: dict) -> None:
        """Handle an error with context information."""
        pass

    @abstractmethod
    async def retry_operation(self, operation: Callable[..., Any], max_retries: int = 3) -> Any:
        """Retry an operation with exponential backoff."""
        pass
