"""MCP Note Management Tools"""

import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.link import Link, LinkCreate
from ...models.note import Note, NoteCreate, NoteUpdate
from ...services.database import DatabaseService
from ...services.semantic_search import SemanticSearchService


class NoteCreateRequest(BaseModel):
    """Note creation request"""
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    tags: list[str] = Field(default_factory=list, description="Note tags")
    source: str | None = Field(None, description="Note source")


class NoteUpdateRequest(BaseModel):
    """Note update request"""
    title: str | None = Field(None, description="Note title")
    content: str | None = Field(None, description="Note content")
    tags: list[str] | None = Field(None, description="Note tags")


class LinkRequest(BaseModel):
    """Link creation request"""
    source_note_id: UUID = Field(..., description="Source note ID")
    target_note_id: UUID = Field(..., description="Target note ID")
    link_type: str = Field("semantic", description="Link type")
    strength: float = Field(0.8, description="Link strength")
    description: str | None = Field(None, description="Link description")


class NoteTools:
    """Note management tools for BrainForge library"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.search_service = SemanticSearchService(database_service)
        self.logger = logging.getLogger(__name__)

    async def create_note(
        self,
        title: str,
        content: str,
        tags: list[str] = None,
        source: str = None
    ) -> dict[str, Any]:
        """Create a new note in the BrainForge library"""

        try:
            note_create = NoteCreate(
                title=title,
                content=content,
                tags=tags or [],
                source=source
            )

            async with self.database_service.session() as session:
                # Create the note
                db_note = await self.database_service.create(
                    session, "notes", note_create.dict()
                )
                note = Note.from_orm(db_note)

                # Generate embedding for semantic search
                await self.search_service.index_note(note)

                return {
                    "note_id": note.id,
                    "title": note.title,
                    "content_preview": note.content[:100] + "..." if len(note.content) > 100 else note.content,
                    "tags": note.tags or [],
                    "created_at": note.created_at.isoformat() if note.created_at else "Unknown",
                    "status": "created"
                }

        except Exception as e:
            self.logger.error(f"Note creation failed: {e}")
            return {
                "error": f"Failed to create note: {str(e)}",
                "status": "failed"
            }

    async def update_note(
        self,
        note_id: UUID,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None
    ) -> dict[str, Any]:
        """Update an existing note in the BrainForge library"""

        try:
            # Build update data
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if content is not None:
                update_data["content"] = content
            if tags is not None:
                update_data["tags"] = tags

            if not update_data:
                return {
                    "note_id": str(note_id),
                    "status": "no_changes",
                    "message": "No changes provided"
                }

            note_update = NoteUpdate(**update_data)

            async with self.database_service.session() as session:
                # Update the note
                db_note = await self.database_service.update(
                    session, "notes", note_id, note_update.dict(exclude_unset=True)
                )

                if not db_note:
                    return {
                        "note_id": str(note_id),
                        "status": "not_found",
                        "error": "Note not found"
                    }

                note = Note.from_orm(db_note)

                # Re-index the note for semantic search
                await self.search_service.index_note(note)

                return {
                    "note_id": note.id,
                    "title": note.title,
                    "content_preview": note.content[:100] + "..." if len(note.content) > 100 else note.content,
                    "tags": note.tags or [],
                    "updated_at": note.updated_at.isoformat() if note.updated_at else "Unknown",
                    "status": "updated"
                }

        except Exception as e:
            self.logger.error(f"Note update failed: {e}")
            return {
                "note_id": str(note_id),
                "error": f"Failed to update note: {str(e)}",
                "status": "failed"
            }

    async def link_notes(
        self,
        source_note_id: UUID,
        target_note_id: UUID,
        link_type: str = "semantic",
        strength: float = 0.8,
        description: str | None = None
    ) -> dict[str, Any]:
        """Create semantic links between notes"""

        try:
            # Validate that both notes exist
            async with self.database_service.session() as session:
                source_note = await self.database_service.get_by_id(session, "notes", source_note_id)
                target_note = await self.database_service.get_by_id(session, "notes", target_note_id)

                if not source_note or not target_note:
                    return {
                        "error": "One or both notes not found",
                        "source_note_found": bool(source_note),
                        "target_note_found": bool(target_note),
                        "status": "failed"
                    }

                # Check if link already exists
                existing_links = await self.database_service.get_all(
                    session,
                    "links",
                    filters={
                        "source_note_id": source_note_id,
                        "target_note_id": target_note_id
                    }
                )

                if existing_links:
                    return {
                        "link_id": existing_links[0].id,
                        "source_note_id": source_note_id,
                        "target_note_id": target_note_id,
                        "link_type": existing_links[0].link_type,
                        "status": "already_exists",
                        "message": "Link already exists"
                    }

                # Create the link
                link_create = LinkCreate(
                    source_note_id=source_note_id,
                    target_note_id=target_note_id,
                    link_type=link_type,
                    strength=strength,
                    description=description
                )

                db_link = await self.database_service.create(
                    session, "links", link_create.dict()
                )
                link = Link.from_orm(db_link)

                return {
                    "link_id": link.id,
                    "source_note_id": source_note_id,
                    "target_note_id": target_note_id,
                    "link_type": link_type,
                    "strength": strength,
                    "description": description,
                    "created_at": link.created_at.isoformat() if link.created_at else "Unknown",
                    "status": "created"
                }

        except Exception as e:
            self.logger.error(f"Link creation failed: {e}")
            return {
                "source_note_id": str(source_note_id),
                "target_note_id": str(target_note_id),
                "error": f"Failed to create link: {str(e)}",
                "status": "failed"
            }

    async def get_note(self, note_id: UUID) -> dict[str, Any]:
        """Retrieve a specific note by ID"""

        try:
            async with self.database_service.session() as session:
                db_note = await self.database_service.get_by_id(session, "notes", note_id)

                if not db_note:
                    return {
                        "note_id": str(note_id),
                        "error": "Note not found",
                        "status": "not_found"
                    }

                note = Note.from_orm(db_note)

                return {
                    "note_id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "tags": note.tags or [],
                    "source": note.source,
                    "created_at": note.created_at.isoformat() if note.created_at else "Unknown",
                    "updated_at": note.updated_at.isoformat() if note.updated_at else "Unknown",
                    "status": "found"
                }

        except Exception as e:
            self.logger.error(f"Failed to get note: {e}")
            return {
                "note_id": str(note_id),
                "error": f"Failed to get note: {str(e)}",
                "status": "failed"
            }

    async def delete_note(self, note_id: UUID) -> dict[str, Any]:
        """Delete a note from the library"""

        try:
            async with self.database_service.session() as session:
                # Check if note exists
                db_note = await self.database_service.get_by_id(session, "notes", note_id)
                if not db_note:
                    return {
                        "note_id": str(note_id),
                        "error": "Note not found",
                        "status": "not_found"
                    }

                # Delete associated links first
                outgoing_links = await self.database_service.get_all(
                    session, "links", filters={"source_note_id": note_id}
                )
                incoming_links = await self.database_service.get_all(
                    session, "links", filters={"target_note_id": note_id}
                )

                for link in outgoing_links + incoming_links:
                    await self.database_service.delete(session, "links", link.id)

                # Delete the note
                await self.database_service.delete(session, "notes", note_id)

                return {
                    "note_id": str(note_id),
                    "deleted_links": len(outgoing_links) + len(incoming_links),
                    "status": "deleted"
                }

        except Exception as e:
            self.logger.error(f"Failed to delete note: {e}")
            return {
                "note_id": str(note_id),
                "error": f"Failed to delete note: {str(e)}",
                "status": "failed"
            }

    async def get_note_links(self, note_id: UUID) -> dict[str, Any]:
        """Get all links for a specific note"""

        try:
            async with self.database_service.session() as session:
                # Get note
                note = await self.database_service.get_by_id(session, "notes", note_id)
                if not note:
                    return {
                        "note_id": str(note_id),
                        "error": "Note not found",
                        "status": "failed"
                    }

                # Get outgoing links (where this note is the source)
                outgoing_links = await self.database_service.get_all(
                    session, "links", filters={"source_note_id": note_id}
                )

                # Get incoming links (where this note is the target)
                incoming_links = await self.database_service.get_all(
                    session, "links", filters={"target_note_id": note_id}
                )

                # Format results
                outgoing_formatted = []
                for link in outgoing_links:
                    target_note = await self.database_service.get_by_id(session, "notes", link.target_note_id)
                    outgoing_formatted.append({
                        "link_id": link.id,
                        "target_note_id": link.target_note_id,
                        "target_note_title": target_note.title if target_note else "Unknown",
                        "link_type": link.link_type,
                        "strength": link.strength,
                        "description": link.description
                    })

                incoming_formatted = []
                for link in incoming_links:
                    source_note = await self.database_service.get_by_id(session, "notes", link.source_note_id)
                    incoming_formatted.append({
                        "link_id": link.id,
                        "source_note_id": link.source_note_id,
                        "source_note_title": source_note.title if source_note else "Unknown",
                        "link_type": link.link_type,
                        "strength": link.strength,
                        "description": link.description
                    })

                return {
                    "note_id": note_id,
                    "note_title": note.title,
                    "outgoing_links": outgoing_formatted,
                    "incoming_links": incoming_formatted,
                    "total_links": len(outgoing_formatted) + len(incoming_formatted),
                    "status": "success"
                }

        except Exception as e:
            self.logger.error(f"Failed to get note links: {e}")
            return {
                "note_id": str(note_id),
                "error": f"Failed to get note links: {str(e)}",
                "status": "failed"
            }
