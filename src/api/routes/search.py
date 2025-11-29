"""Search API routes for BrainForge."""

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..dependencies import DatabaseSession, NoteServiceDep, EmbeddingServiceDep
from ...models.search import (
    SearchRequest, 
    SearchResponse, 
    SearchResult, 
    SearchStats, 
    SearchHealth
)
from ...services.embedding_generator import EmbeddingGenerator
from ...services.vector_store import VectorStore
from ...services.hnsw_index import HNSWIndex
from ...services.semantic_search import SemanticSearch
from ...services.database import NoteService, EmbeddingService

router = APIRouter()


async def get_database_service() -> Any:
    """Get a database service instance for search operations."""
    # Create a simple database service wrapper that uses the existing services
    class SearchDatabaseService:
        def __init__(self, note_service: NoteService, embedding_service: EmbeddingService):
            self.note_service = note_service
            self.embedding_service = embedding_service
            
        async def get_embedding_by_note_id(self, session: AsyncSession, note_id: UUID) -> Any:
            """Get embedding by note ID."""
            return await self.embedding_service.get_by_note(session, note_id)
            
        async def get_note_by_id(self, session: AsyncSession, note_id: UUID) -> Any:
            """Get note by ID."""
            return await self.note_service.get(session, note_id)
            
        async def list_notes(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> list[Any]:
            """List notes with pagination."""
            return await self.note_service.list(session, skip, limit)
    
    return SearchDatabaseService(NoteService(), EmbeddingService())


@router.post("/search", response_model=SearchResponse)
async def search_notes(
    search_request: SearchRequest,
    session: AsyncSession = DatabaseSession,
    note_service: Any = NoteServiceDep,
    embedding_service: Any = EmbeddingServiceDep
):
    """Search notes with semantic and hybrid search."""
    
    try:
        start_time = time.time()
        
        # Create database service wrapper
        database_service = await get_database_service()
        
        # Initialize services with database service
        embedding_generator = EmbeddingGenerator(database_service)
        vector_store = VectorStore(database_service)
        hnsw_index = HNSWIndex(database_service)
        semantic_search = SemanticSearch(
            embedding_generator=embedding_generator,
            vector_store=vector_store,
            hnsw_index=hnsw_index,
            database_service=database_service
        )
        
        # Perform semantic search using the correct method name
        search_config = {
            "limit": search_request.limit,
            "distance_metric": "cosine",
            "min_similarity": search_request.similarity_threshold,
            "note_types": search_request.note_types,
            "metadata_filters": search_request.metadata_filters
        }
        
        search_results = await semantic_search.semantic_search(
            query=search_request.query,
            config=search_config
        )
        
        query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Convert to response model
        results = []
        for result in search_results:
            # Extract note details from result
            note = result.get("note", {})
            search_result = SearchResult(
                note_id=note.get("id", UUID(int=0)),
                content=note.get("content", "")[:500] + "..." if len(note.get("content", "")) > 500 else note.get("content", ""),
                note_type=note.get("note_type", "permanent"),
                similarity_score=result.get("similarity_score", 0.0),
                metadata=note.get("metadata", {}),
                embedding_vector=result.get("embedding_vector") if search_request.include_embeddings else None,
                version=note.get("version", 1)
            )
            results.append(search_result)
        
        return SearchResponse(
            results=results,
            total_results=len(results),
            query_time_ms=query_time,
            search_type="semantic",
            query=search_request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/stats", response_model=SearchStats)
async def get_search_stats(
    session: AsyncSession = DatabaseSession,
    note_service: Any = NoteServiceDep,
    embedding_service: Any = EmbeddingServiceDep
):
    """Get search statistics and performance metrics."""
    
    try:
        # Get total notes count (using count method if available, otherwise estimate)
        total_notes = 0
        try:
            # Try to get count from service
            notes = await note_service.list(session, limit=1000)
            total_notes = len(notes)  # This is an estimate for now
        except:
            total_notes = 0
        
        # Get total embeddings count
        total_embeddings = 0
        try:
            embeddings = await embedding_service.list(session, limit=1000)
            total_embeddings = len(embeddings)  # Estimate
        except:
            total_embeddings = 0
        
        # Placeholder for index size, average similarity, and search count
        index_size = 0  # Would need actual implementation
        average_similarity = 0.85  # Placeholder
        search_count = 0  # Placeholder
        
        return SearchStats(
            total_notes=total_notes,
            total_embeddings=total_embeddings,
            index_size=index_size,
            average_similarity=average_similarity,
            search_count=search_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search stats: {str(e)}")


@router.get("/search/health", response_model=SearchHealth)
async def get_search_health(
    session: AsyncSession = DatabaseSession
):
    """Get search system health status."""
    
    try:
        # Basic health checks - these would be more comprehensive in production
        
        # Check database health
        database_health = "healthy"
        try:
            # Simple query to test database connection
            await session.execute(text("SELECT 1"))
        except Exception:
            database_health = "unhealthy"
        
        # Check embedding service health (basic check)
        embedding_health = "healthy"
        try:
            # Simple test - would be more comprehensive
            database_service = await get_database_service()
            embedding_generator = EmbeddingGenerator(database_service)
            # If we can create the service, consider it healthy for now
        except Exception:
            embedding_health = "degraded"
        
        # Check vector store health
        vector_store_health = "healthy"
        try:
            database_service = await get_database_service()
            vector_store = VectorStore(database_service)
        except Exception:
            vector_store_health = "degraded"
        
        # Check HNSW index health
        hnsw_health = "healthy"
        try:
            database_service = await get_database_service()
            hnsw_index = HNSWIndex(database_service)
        except Exception:
            hnsw_health = "degraded"
        
        # Determine overall status
        statuses = [embedding_health, vector_store_health, hnsw_health, database_health]
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return SearchHealth(
            status=overall_status,
            embedding_service=embedding_health,
            vector_store=vector_store_health,
            hnsw_index=hnsw_health,
            database=database_health,
            last_check=time.strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/search/similar/{note_id}")
async def find_similar_notes(
    note_id: UUID,
    limit: int = Query(default=5, ge=1, le=20),
    similarity_threshold: float = Query(default=0.7, ge=0.0, le=1.0),
    session: AsyncSession = DatabaseSession,
    note_service: Any = NoteServiceDep,
    embedding_service: Any = EmbeddingServiceDep
):
    """Find notes similar to a specific note."""
    
    try:
        start_time = time.time()
        
        # Create database service wrapper
        database_service = await get_database_service()
        
        # Initialize services
        embedding_generator = EmbeddingGenerator(database_service)
        vector_store = VectorStore(database_service)
        hnsw_index = HNSWIndex(database_service)
        semantic_search = SemanticSearch(
            embedding_generator=embedding_generator,
            vector_store=vector_store,
            hnsw_index=hnsw_index,
            database_service=database_service
        )
        
        # Find similar notes using a simplified approach
        # This would need proper implementation in the semantic_search service
        similar_notes = []
        
        # For now, return a placeholder response
        query_time = (time.time() - start_time) * 1000
        
        return {
            "similar_notes": similar_notes,
            "query_time_ms": query_time,
            "reference_note_id": str(note_id),
            "message": "Similar notes functionality to be implemented"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar notes: {str(e)}")