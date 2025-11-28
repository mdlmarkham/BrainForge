"""Note synchronization service between BrainForge and Obsidian."""

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .obsidian import ObsidianService, ObsidianNote
from src.models.orm.note import Note as ORMNote, NoteType
from src.models.note import Note as PydanticNote, NoteCreate, NoteUpdate


class SyncDirection(Enum):
    """Direction of synchronization."""
    BRAINFORGE_TO_OBSIDIAN = "brainforge_to_obsidian"
    OBSIDIAN_TO_BRAINFORGE = "obsidian_to_brainforge"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """Status of a sync operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CONFLICT = "conflict"


class ConflictResolution(Enum):
    """Conflict resolution strategy."""
    KEEP_BRAINFORGE = "keep_brainforge"
    KEEP_OBSIDIAN = "keep_obsidian"
    MERGE = "merge"
    SKIP = "skip"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    status: SyncStatus
    processed: int
    created: int
    updated: int
    conflicts: int
    errors: int
    message: str
    details: Dict[str, Any]


@dataclass
class SyncConfig:
    """Configuration for synchronization."""
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.KEEP_BRAINFORGE
    dry_run: bool = False
    incremental: bool = True
    max_notes: Optional[int] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class SyncService:
    """Service for synchronizing notes between BrainForge and Obsidian."""
    
    def __init__(self, db_session: AsyncSession, obsidian_service: ObsidianService):
        self.db_session = db_session
        self.obsidian_service = obsidian_service
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of note content for change detection."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_note_type_from_path(self, path: str) -> NoteType:
        """Extract note type from file path."""
        if '/fleeting/' in path or path.startswith('fleeting/'):
            return NoteType.FLEETING
        elif '/literature/' in path or path.startswith('literature/'):
            return NoteType.LITERATURE
        elif '/permanent/' in path or path.startswith('permanent/'):
            return NoteType.PERMANENT
        elif '/insight/' in path or path.startswith('insight/'):
            return NoteType.INSIGHT
        else:
            return NoteType.PERMANENT  # Default to permanent
    
    def _create_frontmatter(self, note: ORMNote) -> Dict[str, Any]:
        """Create Obsidian frontmatter from BrainForge note."""
        # Convert SQLAlchemy model to dict for frontmatter
        frontmatter = {
            "id": str(note.id),
            "type": note.note_type.value,
            "created": note.created_at.isoformat() if note.created_at else datetime.now(timezone.utc).isoformat(),
            "updated": note.updated_at.isoformat() if note.updated_at else datetime.now(timezone.utc).isoformat(),
            "created_by": note.created_by or "obsidian_sync",
            "brainforge": True,  # Mark as synced from BrainForge
        }
        
        # Add metadata if available
        # Check if note_metadata has content and convert to dict
        metadata_value = getattr(note, 'note_metadata', None)
        if metadata_value and isinstance(metadata_value, dict):
            frontmatter.update(metadata_value)
        
        return frontmatter
    
    def _parse_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Obsidian frontmatter for BrainForge metadata."""
        metadata = frontmatter.copy()
        
        # Remove BrainForge-specific fields
        metadata.pop("id", None)
        metadata.pop("type", None)
        metadata.pop("created", None)
        metadata.pop("updated", None)
        metadata.pop("created_by", None)
        metadata.pop("brainforge", None)
        
        return metadata
    
    async def _get_brainforge_notes(self) -> List[ORMNote]:
        """Get all notes from BrainForge database."""
        result = await self.db_session.execute(select(ORMNote))
        return list(result.scalars().all())
    
    async def _get_obsidian_notes(self) -> List[ObsidianNote]:
        """Get all notes from Obsidian vault."""
        files = await self.obsidian_service.list_vault_files()
        notes = []
        
        for file_path in files:
            if file_path.endswith('.md'):
                try:
                    note = await self.obsidian_service.get_note(file_path, as_json=True)
                    notes.append(note)
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        return notes
    
    async def _create_brainforge_note(self, obsidian_note: ObsidianNote) -> ORMNote:
        """Create a BrainForge note from Obsidian note."""
        note_type = self._extract_note_type_from_path(obsidian_note.path)
        metadata = self._parse_frontmatter(obsidian_note.frontmatter)
        
        # Create the note using SQLAlchemy ORM
        note = ORMNote(
            content=obsidian_note.content,
            note_type=note_type,
            note_metadata=metadata,
            created_by="obsidian_sync",  # Default creator for synced notes
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db_session.add(note)
        await self.db_session.flush()
        return note
    
    async def _update_brainforge_note(self, brainforge_note: ORMNote, obsidian_note: ObsidianNote) -> ORMNote:
        """Update a BrainForge note with Obsidian content."""
        # Update SQLAlchemy ORM model attributes
        # Update content using setattr for SQLAlchemy compatibility
        setattr(brainforge_note, 'content', obsidian_note.content)
        
        # Handle metadata update
        current_metadata = brainforge_note.note_metadata or {}
        parsed_metadata = self._parse_frontmatter(obsidian_note.frontmatter)
        current_metadata.update(parsed_metadata)
        # Update metadata using setattr for SQLAlchemy compatibility
        setattr(brainforge_note, 'note_metadata', current_metadata)
        
        brainforge_note.updated_at = datetime.now(timezone.utc)
        
        return brainforge_note
    
    async def _create_obsidian_note(self, brainforge_note: ORMNote) -> None:
        """Create an Obsidian note from BrainForge note."""
        # Determine file path based on note type
        base_path = brainforge_note.note_type.value
        filename = f"{brainforge_note.id}.md"
        file_path = f"{base_path}/{filename}"
        
        # Create frontmatter
        frontmatter = self._create_frontmatter(brainforge_note)
        
        # Format as YAML frontmatter
        frontmatter_yaml = "---\n"
        for key, value in frontmatter.items():
            frontmatter_yaml += f"{key}: {repr(value)}\n"
        frontmatter_yaml += "---\n\n"
        
        # Combine frontmatter and content
        full_content = frontmatter_yaml + brainforge_note.content
        
        # Convert content to string for Obsidian API
        content_str = str(brainforge_note.content) if hasattr(brainforge_note.content, '__str__') else str(full_content)
        await self.obsidian_service.create_or_append_note(file_path, content_str)
    
    async def _update_obsidian_note(self, brainforge_note: ORMNote, obsidian_note: ObsidianNote) -> None:
        """Update an Obsidian note with BrainForge content."""
        # Create updated frontmatter
        frontmatter = self._create_frontmatter(brainforge_note)
        
        # Format as YAML frontmatter
        frontmatter_yaml = "---\n"
        for key, value in frontmatter.items():
            frontmatter_yaml += f"{key}: {repr(value)}\n"
        frontmatter_yaml += "---\n\n"
        
        # Combine frontmatter and content
        full_content = frontmatter_yaml + brainforge_note.content
        
        # Replace the entire note content
        # Convert content to string for Obsidian API
        content_str = str(brainforge_note.content) if hasattr(brainforge_note.content, '__str__') else str(full_content)
        await self.obsidian_service.create_or_append_note(obsidian_note.path, content_str)
    
    async def _detect_conflicts(self, brainforge_note: ORMNote, obsidian_note: ObsidianNote) -> bool:
        """Detect if there are conflicts between BrainForge and Obsidian versions."""
        if not brainforge_note.updated_at or not obsidian_note.stat.get('mtime'):
            return False
        
        # Compare modification times
        brainforge_time = brainforge_note.updated_at
        obsidian_time = datetime.fromtimestamp(obsidian_note.stat.get('mtime', 0), timezone.utc)
        
        # If both were modified recently, check content
        time_diff = abs((brainforge_time - obsidian_time).total_seconds())
        if time_diff < 300:  # 5 minutes threshold
            # Get content as string for hash calculation
            content_str = str(brainforge_note.content) if hasattr(brainforge_note.content, '__str__') else ""
            brainforge_hash = self._calculate_content_hash(content_str)
            obsidian_hash = self._calculate_content_hash(obsidian_note.content)
            return brainforge_hash != obsidian_hash
        
        return False
    
    async def sync_notes(self, config: SyncConfig) -> SyncResult:
        """Synchronize notes between BrainForge and Obsidian."""
        processed = 0
        created = 0
        updated = 0
        conflicts = 0
        errors = 0
        
        try:
            # Get notes from both sources
            brainforge_notes = await self._get_brainforge_notes()
            obsidian_notes = await self._get_obsidian_notes()
            
            # Create mapping for quick lookup
            brainforge_by_path = {}
            obsidian_by_id = {}
            
            # Map BrainForge notes by their expected Obsidian path
            for note in brainforge_notes:
                base_path = note.note_type.value
                filename = f"{note.id}.md"
                file_path = f"{base_path}/{filename}"
                brainforge_by_path[file_path] = note
            
            # Map Obsidian notes by BrainForge ID from frontmatter
            for note in obsidian_notes:
                brainforge_id = note.frontmatter.get('id')
                if brainforge_id:
                    obsidian_by_id[brainforge_id] = note
            
            # Perform synchronization based on direction
            if config.direction in [SyncDirection.BIDIRECTIONAL, SyncDirection.OBSIDIAN_TO_BRAINFORGE]:
                # Sync from Obsidian to BrainForge
                for obsidian_note in obsidian_notes:
                    try:
                        processed += 1
                        brainforge_id = obsidian_note.frontmatter.get('id')
                        
                        if brainforge_id and brainforge_id in obsidian_by_id:
                            # Update existing note
                            brainforge_note = brainforge_by_path.get(obsidian_note.path)
                            if brainforge_note:
                                if await self._detect_conflicts(brainforge_note, obsidian_note):
                                    conflicts += 1
                                    # Apply conflict resolution
                                    if config.conflict_resolution == ConflictResolution.KEEP_OBSIDIAN:
                                        await self._update_brainforge_note(brainforge_note, obsidian_note)
                                        updated += 1
                                    elif config.conflict_resolution == ConflictResolution.MERGE:
                                        # Simple merge: keep both contents separated
                                        merged_content = f"# BrainForge Version\n\n{brainforge_note.content}\n\n# Obsidian Version\n\n{obsidian_note.content}"
                                        brainforge_note.content = merged_content
                                        updated += 1
                                    # Skip if KEEP_BRAINFORGE or SKIP
                                else:
                                    await self._update_brainforge_note(brainforge_note, obsidian_note)
                                    updated += 1
                        else:
                            # Create new note
                            if not config.dry_run:
                                await self._create_brainforge_note(obsidian_note)
                            created += 1
                    
                    except Exception as e:
                        errors += 1
                        continue
            
            if config.direction in [SyncDirection.BIDIRECTIONAL, SyncDirection.BRAINFORGE_TO_OBSIDIAN]:
                # Sync from BrainForge to Obsidian
                for brainforge_note in brainforge_notes:
                    try:
                        processed += 1
                        base_path = brainforge_note.note_type.value
                        filename = f"{brainforge_note.id}.md"
                        file_path = f"{base_path}/{filename}"
                        
                        obsidian_note = obsidian_by_id.get(str(brainforge_note.id))
                        if obsidian_note:
                            # Update existing note
                            if await self._detect_conflicts(brainforge_note, obsidian_note):
                                conflicts += 1
                                # Apply conflict resolution
                                if config.conflict_resolution == ConflictResolution.KEEP_BRAINFORGE:
                                    if not config.dry_run:
                                        await self._update_obsidian_note(brainforge_note, obsidian_note)
                                    updated += 1
                                elif config.conflict_resolution == ConflictResolution.MERGE:
                                    # Simple merge: keep both contents separated
                                    merged_content = f"# BrainForge Version\n\n{brainforge_note.content}\n\n# Obsidian Version\n\n{obsidian_note.content}"
                                    # Update content using setattr for SQLAlchemy compatibility
                                    setattr(brainforge_note, 'content', merged_content)
                                    if not config.dry_run:
                                        await self._update_obsidian_note(brainforge_note, obsidian_note)
                                    updated += 1
                                # Skip if KEEP_OBSIDIAN or SKIP
                            else:
                                if not config.dry_run:
                                    await self._update_obsidian_note(brainforge_note, obsidian_note)
                                updated += 1
                        else:
                            # Create new note
                            if not config.dry_run:
                                await self._create_obsidian_note(brainforge_note)
                            created += 1
                    
                    except Exception as e:
                        errors += 1
                        continue
            
            # Commit changes if not dry run
            if not config.dry_run:
                await self.db_session.commit()
            
            # Determine status
            if errors == 0 and conflicts == 0:
                status = SyncStatus.SUCCESS
                message = f"Sync completed: {created} created, {updated} updated"
            elif errors > 0 or conflicts > 0:
                status = SyncStatus.PARTIAL
                message = f"Sync completed with issues: {created} created, {updated} updated, {conflicts} conflicts, {errors} errors"
            else:
                status = SyncStatus.FAILED
                message = "Sync failed"
            
            return SyncResult(
                status=status,
                processed=processed,
                created=created,
                updated=updated,
                conflicts=conflicts,
                errors=errors,
                message=message,
                details={
                    "brainforge_notes_count": len(brainforge_notes),
                    "obsidian_notes_count": len(obsidian_notes),
                    "dry_run": config.dry_run
                }
            )
        
        except Exception as e:
            await self.db_session.rollback()
            return SyncResult(
                status=SyncStatus.FAILED,
                processed=processed,
                created=created,
                updated=updated,
                conflicts=conflicts,
                errors=errors + 1,
                message=f"Sync failed: {str(e)}",
                details={"error": str(e)}
            )