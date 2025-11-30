"""Search models for BrainForge semantic search functionality."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .note import NoteType


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score (0-1)")
    note_types: list[NoteType] | None = Field(default=None, description="Filter by note types")
    metadata_filters: dict[str, Any] | None = Field(default=None, description="Metadata field filters")
    include_embeddings: bool = Field(default=False, description="Include embedding vectors in response")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()

    @field_validator('metadata_filters')
    @classmethod
    def validate_metadata_filters(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate metadata filters structure."""
        if v is None:
            return None

        if not isinstance(v, dict):
            raise ValueError("Metadata filters must be a dictionary")

        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Metadata filter keys must be strings")
            if not isinstance(value, (str, int, float, bool, list, dict)) and value is not None:
                raise ValueError(f"Metadata filter value for key '{key}' must be a valid JSON type")

        return v


class SearchResult(BaseModel):
    """Individual search result model."""

    note_id: UUID = Field(..., description="Note ID")
    content: str = Field(..., description="Note content (truncated if needed)")
    note_type: NoteType = Field(..., description="Note type")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score (0-1)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Note metadata")
    embedding_vector: list[float] | None = Field(default=None, description="Embedding vector (if requested)")
    version: int = Field(..., ge=1, description="Note version")

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Response model for semantic search."""

    results: list[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total number of matching results")
    query_time_ms: float = Field(..., ge=0.0, description="Query execution time in milliseconds")
    search_type: str = Field(..., description="Type of search performed (semantic/hybrid)")
    query: str = Field(..., description="Original search query")


class SearchStats(BaseModel):
    """Search statistics model."""

    total_notes: int = Field(..., ge=0, description="Total number of notes in database")
    total_embeddings: int = Field(..., ge=0, description="Total number of embeddings")
    index_size: int = Field(..., ge=0, description="Size of HNSW index in bytes")
    average_similarity: float = Field(..., ge=0.0, le=1.0, description="Average similarity score across all searches")
    search_count: int = Field(..., ge=0, description="Total number of searches performed")


class SearchHealth(BaseModel):
    """Search health status model."""

    status: str = Field(..., description="Health status (healthy/degraded/unhealthy)")
    embedding_service: str = Field(..., description="Embedding service status")
    vector_store: str = Field(..., description="Vector store status")
    hnsw_index: str = Field(..., description="HNSW index status")
    database: str = Field(..., description="Database connection status")
    last_check: str = Field(..., description="Last health check timestamp")
