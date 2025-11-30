"""MCP Search and Discovery Tools"""

import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ...services.database import DatabaseService
from ...services.semantic_search import SemanticSearchService


class SearchQuery(BaseModel):
    """Search query parameters"""
    query: str = Field(..., description="Search query text")
    limit: int = Field(10, description="Maximum number of results")
    similarity_threshold: float = Field(0.7, description="Minimum similarity score")
    include_content: bool = Field(True, description="Include note content in results")


class SearchResult(BaseModel):
    """Search result"""
    note_id: UUID
    title: str
    content_preview: str
    similarity_score: float
    tags: list[str] = Field(default_factory=list)
    created_at: str


class ConnectionDiscovery(BaseModel):
    """Semantic connection between notes"""
    source_note_id: UUID
    target_note_id: UUID
    connection_strength: float
    connection_type: str
    shared_tags: list[str]
    semantic_similarity: float


class LibraryStats(BaseModel):
    """Library statistics"""
    total_notes: int
    total_links: int
    average_note_length: float
    most_common_tags: list[dict[str, Any]]
    recent_activity: dict[str, int]


class SearchTools:
    """Search and discovery tools for BrainForge library"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.search_service = SemanticSearchService(database_service)
        self.logger = logging.getLogger(__name__)

    async def search_library(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        include_content: bool = True
    ) -> dict[str, Any]:
        """Search the BrainForge library using semantic search"""

        try:
            # Perform semantic search
            search_results = await self.search_service.search_notes(
                query=query,
                limit=limit,
                similarity_threshold=similarity_threshold
            )

            # Format results
            formatted_results = []
            for result in search_results:
                note_data = {
                    "note_id": result.note.id,
                    "title": result.note.title,
                    "content_preview": result.note.content[:200] + "..." if len(result.note.content) > 200 else result.note.content,
                    "similarity_score": result.similarity_score,
                    "tags": result.note.tags or [],
                    "created_at": result.note.created_at.isoformat() if result.note.created_at else "Unknown"
                }
                formatted_results.append(note_data)

            return {
                "query": query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "search_parameters": {
                    "limit": limit,
                    "similarity_threshold": similarity_threshold,
                    "include_content": include_content
                }
            }

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {
                "query": query,
                "total_results": 0,
                "results": [],
                "error": str(e)
            }

    async def discover_connections(
        self,
        note_id: UUID | None = None,
        connection_threshold: float = 0.6,
        max_connections: int = 20
    ) -> dict[str, Any]:
        """Discover semantic connections between library items"""

        try:
            connections = []

            if note_id:
                # Discover connections for a specific note
                connections = await self._discover_note_connections(
                    note_id, connection_threshold, max_connections
                )
            else:
                # Discover global connections
                connections = await self._discover_global_connections(
                    connection_threshold, max_connections
                )

            return {
                "connections_found": len(connections),
                "connections": connections,
                "discovery_parameters": {
                    "note_id": str(note_id) if note_id else "global",
                    "connection_threshold": connection_threshold,
                    "max_connections": max_connections
                }
            }

        except Exception as e:
            self.logger.error(f"Connection discovery failed: {e}")
            return {
                "connections_found": 0,
                "connections": [],
                "error": str(e)
            }

    async def _discover_note_connections(
        self,
        note_id: UUID,
        threshold: float,
        max_connections: int
    ) -> list[dict[str, Any]]:
        """Discover connections for a specific note"""

        # Get the target note
        async with self.database_service.session() as session:
            target_note = await self.database_service.get_by_id(session, "notes", note_id)
            if not target_note:
                return []

            # Find semantically similar notes
            similar_notes = await self.search_service.find_similar_notes(
                note_id=note_id,
                limit=max_connections,
                similarity_threshold=threshold
            )

            connections = []
            for similar_note in similar_notes:
                connection = {
                    "source_note_id": note_id,
                    "target_note_id": similar_note.note.id,
                    "connection_strength": similar_note.similarity_score,
                    "connection_type": "semantic_similarity",
                    "shared_tags": self._find_shared_tags(target_note, similar_note.note),
                    "semantic_similarity": similar_note.similarity_score
                }
                connections.append(connection)

            return connections

    async def _discover_global_connections(
        self,
        threshold: float,
        max_connections: int
    ) -> list[dict[str, Any]]:
        """Discover global connections across the library"""

        # This would be a more complex implementation
        # For now, return a simplified version
        async with self.database_service.session() as session:
            # Get recent notes to analyze
            recent_notes = await self.database_service.get_all(
                session, "notes", limit=min(10, max_connections), order_by="created_at DESC"
            )

            connections = []
            for i, note1 in enumerate(recent_notes):
                for j, note2 in enumerate(recent_notes):
                    if i < j:  # Avoid duplicate connections
                        # Simple tag-based connection discovery
                        shared_tags = self._find_shared_tags(note1, note2)
                        if shared_tags:
                            connection_strength = len(shared_tags) / max(len(note1.tags or []), len(note2.tags or []), 1)

                            if connection_strength >= threshold:
                                connection = {
                                    "source_note_id": note1.id,
                                    "target_note_id": note2.id,
                                    "connection_strength": connection_strength,
                                    "connection_type": "tag_similarity",
                                    "shared_tags": shared_tags,
                                    "semantic_similarity": connection_strength
                                }
                                connections.append(connection)
                                if len(connections) >= max_connections:
                                    return connections

            return connections

    def _find_shared_tags(self, note1, note2) -> list[str]:
        """Find shared tags between two notes"""
        tags1 = set(note1.tags or [])
        tags2 = set(note2.tags or [])
        return list(tags1.intersection(tags2))

    async def get_library_stats(self) -> dict[str, Any]:
        """Get statistics about the BrainForge library"""

        try:
            async with self.database_service.session() as session:
                # Get total notes
                total_notes = await self.database_service.count(session, "notes")

                # Get total links
                total_links = await self.database_service.count(session, "links")

                # Get average note length
                notes = await self.database_service.get_all(session, "notes", limit=100)
                avg_length = sum(len(note.content or "") for note in notes) / max(len(notes), 1)

                # Get most common tags (simplified)
                tag_counts = {}
                for note in notes:
                    for tag in note.tags or []:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

                most_common_tags = [
                    {"tag": tag, "count": count}
                    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                ]

                # Get recent activity (last 7 days - simplified)
                recent_activity = {
                    "notes_created": total_notes,  # Simplified - would need timestamp filtering
                    "links_created": total_links,
                    "searches_performed": 0  # Would need search log
                }

                return {
                    "total_notes": total_notes,
                    "total_links": total_links,
                    "average_note_length": round(avg_length, 2),
                    "most_common_tags": most_common_tags,
                    "recent_activity": recent_activity
                }

        except Exception as e:
            self.logger.error(f"Failed to get library stats: {e}")
            return {
                "total_notes": 0,
                "total_links": 0,
                "average_note_length": 0,
                "most_common_tags": [],
                "recent_activity": {},
                "error": str(e)
            }
