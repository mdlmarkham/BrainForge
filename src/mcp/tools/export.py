"""MCP Export Tools"""

import csv
import json
import logging
from datetime import datetime
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.models.link import Link
from src.models.note import Note
from src.services.generic_database_service import DatabaseService


class ExportRequest(BaseModel):
    """Export request parameters"""
    format: str = Field(..., description="Export format (json, csv, yaml, markdown)")
    include_content: bool = Field(True, description="Include note content in export")
    include_links: bool = Field(True, description="Include links in export")
    tags_filter: list[str] | None = Field(None, description="Filter by tags")
    date_range: dict[str, str] | None = Field(None, description="Date range filter")


class DocumentationRequest(BaseModel):
    """Documentation generation request"""
    output_format: str = Field("markdown", description="Output format")
    include_examples: bool = Field(True, description="Include code examples")
    include_api_reference: bool = Field(True, description="Include API reference")
    template: str | None = Field(None, description="Custom template")


class ExportTools:
    """Export and documentation tools for BrainForge library"""

    def __init__(self, database_service: DatabaseService):
        self.database_service = database_service
        self.logger = logging.getLogger(__name__)

    async def export_library(
        self,
        format: str,
        include_content: bool = True,
        include_links: bool = True,
        tags_filter: list[str] = None,
        date_range: dict[str, str] = None
    ) -> dict[str, Any]:
        """Export the BrainForge library in various formats"""

        try:
            # Validate format
            supported_formats = ["json", "csv", "yaml", "markdown"]
            if format not in supported_formats:
                return {
                    "error": f"Unsupported format. Supported: {supported_formats}",
                    "status": "failed"
                }

            # Get library data
            library_data = await self._get_library_data(
                include_content, include_links, tags_filter, date_range
            )

            # Export in requested format
            export_content = await self._format_export(library_data, format)

            return {
                "format": format,
                "content": export_content,
                "export_info": {
                    "notes_exported": len(library_data.get("notes", [])),
                    "links_exported": len(library_data.get("links", [])),
                    "total_items": len(library_data.get("notes", [])) + len(library_data.get("links", [])),
                    "export_timestamp": datetime.now().isoformat()
                },
                "status": "success"
            }

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return {
                "format": format,
                "error": f"Failed to export library: {str(e)}",
                "status": "failed"
            }

    async def generate_documentation(
        self,
        output_format: str = "markdown",
        include_examples: bool = True,
        include_api_reference: bool = True,
        template: str = None
    ) -> dict[str, Any]:
        """Generate documentation for the library"""

        try:
            # Get library structure and metadata
            library_info = await self._get_library_info()

            # Generate documentation based on format
            documentation = await self._generate_documentation_content(
                library_info, output_format, include_examples, include_api_reference, template
            )

            return {
                "output_format": output_format,
                "documentation": documentation,
                "generation_info": {
                    "sections_generated": len(documentation.get("sections", [])),
                    "total_length": len(str(documentation)),
                    "generation_timestamp": datetime.now().isoformat()
                },
                "status": "success"
            }

        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {
                "output_format": output_format,
                "error": f"Failed to generate documentation: {str(e)}",
                "status": "failed"
            }

    async def _get_library_data(
        self,
        include_content: bool,
        include_links: bool,
        tags_filter: list[str] = None,
        date_range: dict[str, str] = None
    ) -> dict[str, Any]:
        """Get library data for export"""

        library_data = {"notes": [], "links": []}

        async with self.database_service.session() as session:
            # Build filters for notes
            note_filters = {}
            if tags_filter:
                # This would require more sophisticated filtering for array fields
                # For now, we'll get all notes and filter in memory
                pass

            # Get notes
            notes = await self.database_service.get_all(session, "notes")

            for db_note in notes:
                note = Note.from_orm(db_note)

                # Apply tag filtering
                if tags_filter and not any(tag in (note.tags or []) for tag in tags_filter):
                    continue

                # Apply date range filtering
                if date_range and note.created_at:
                    note_date = note.created_at.date().isoformat()
                    if date_range.get("start") and note_date < date_range["start"]:
                        continue
                    if date_range.get("end") and note_date > date_range["end"]:
                        continue

                note_data = {
                    "id": str(note.id),
                    "title": note.title,
                    "tags": note.tags or [],
                    "source": note.source,
                    "created_at": note.created_at.isoformat() if note.created_at else None,
                    "updated_at": note.updated_at.isoformat() if note.updated_at else None
                }

                if include_content:
                    note_data["content"] = note.content

                library_data["notes"].append(note_data)

            # Get links if requested
            if include_links:
                links = await self.database_service.get_all(session, "links")

                for db_link in links:
                    link = Link.from_orm(db_link)
                    link_data = {
                        "id": str(link.id),
                        "source_note_id": str(link.source_note_id),
                        "target_note_id": str(link.target_note_id),
                        "link_type": link.link_type,
                        "strength": link.strength,
                        "description": link.description,
                        "created_at": link.created_at.isoformat() if link.created_at else None
                    }
                    library_data["links"].append(link_data)

        return library_data

    async def _format_export(self, library_data: dict[str, Any], format: str) -> str:
        """Format export data in requested format"""

        if format == "json":
            return json.dumps(library_data, indent=2, ensure_ascii=False)

        elif format == "csv":
            # Create CSV content
            csv_lines = []

            # Notes CSV
            if library_data["notes"]:
                csv_lines.append("NOTES")
                if library_data["notes"]:
                    fieldnames = list(library_data["notes"][0].keys())
                    writer = csv.DictWriter(csv_lines, fieldnames=fieldnames)
                    writer.writeheader()
                    for note in library_data["notes"]:
                        writer.writerow(note)
                csv_lines.append("")

            # Links CSV
            if library_data["links"]:
                csv_lines.append("LINKS")
                if library_data["links"]:
                    fieldnames = list(library_data["links"][0].keys())
                    writer = csv.DictWriter(csv_lines, fieldnames=fieldnames)
                    writer.writeheader()
                    for link in library_data["links"]:
                        writer.writerow(link)

            return "\n".join(csv_lines)

        elif format == "yaml":
            return yaml.dump(library_data, default_flow_style=False, allow_unicode=True)

        elif format == "markdown":
            return self._format_markdown(library_data)

        else:
            return str(library_data)

    def _format_markdown(self, library_data: dict[str, Any]) -> str:
        """Format data as markdown"""

        markdown_lines = ["# BrainForge Library Export", ""]

        # Notes section
        markdown_lines.append("## Notes")
        markdown_lines.append("")

        for note in library_data.get("notes", []):
            markdown_lines.append(f"### {note.get('title', 'Untitled')}")
            markdown_lines.append(f"**ID:** {note.get('id', 'N/A')}")
            markdown_lines.append(f"**Tags:** {', '.join(note.get('tags', []))}")
            markdown_lines.append(f"**Created:** {note.get('created_at', 'Unknown')}")

            if "content" in note:
                markdown_lines.append("")
                markdown_lines.append("#### Content")
                markdown_lines.append(note["content"])

            markdown_lines.append("")

        # Links section
        if library_data.get("links"):
            markdown_lines.append("## Links")
            markdown_lines.append("")

            for link in library_data["links"]:
                markdown_lines.append(f"- **{link.get('link_type', 'link')}**: {link.get('source_note_id')} → {link.get('target_note_id')}")
                if link.get("description"):
                    markdown_lines.append(f"  *Description:* {link['description']}")
                markdown_lines.append(f"  *Strength:* {link.get('strength', 0.0)}")
                markdown_lines.append("")

        return "\n".join(markdown_lines)

    async def _get_library_info(self) -> dict[str, Any]:
        """Get library information for documentation"""

        async with self.database_service.session() as session:
            # Get basic statistics
            total_notes = await self.database_service.count(session, "notes")
            total_links = await self.database_service.count(session, "links")

            # Get tag distribution
            notes = await self.database_service.get_all(session, "notes", limit=100)
            tag_counts = {}
            for note in notes:
                for tag in note.tags or []:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Get recent activity
            recent_notes = await self.database_service.get_all(
                session, "notes", limit=5, order_by="created_at DESC"
            )

            return {
                "statistics": {
                    "total_notes": total_notes,
                    "total_links": total_links,
                    "tag_distribution": tag_counts
                },
                "recent_activity": [
                    {
                        "title": note.title,
                        "created_at": note.created_at.isoformat() if note.created_at else "Unknown",
                        "tags": note.tags or []
                    }
                    for note in recent_notes
                ],
                "export_timestamp": datetime.now().isoformat()
            }

    async def _generate_documentation_content(
        self,
        library_info: dict[str, Any],
        output_format: str,
        include_examples: bool,
        include_api_reference: bool,
        template: str = None
    ) -> dict[str, Any]:
        """Generate documentation content"""

        documentation = {
            "sections": [],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "library_version": "1.0.0",  # Would be dynamic in real implementation
                "format": output_format
            }
        }

        # Overview section
        overview = {
            "title": "Library Overview",
            "content": f"""
# BrainForge Library Documentation

## Overview
The BrainForge library contains {library_info['statistics']['total_notes']} notes 
with {library_info['statistics']['total_links']} semantic connections.

## Statistics
- Total Notes: {library_info['statistics']['total_notes']}
- Total Links: {library_info['statistics']['total_links']}
- Most Common Tags: {', '.join(sorted(library_info['statistics']['tag_distribution'].keys())[:5])}
            """.strip()
        }
        documentation["sections"].append(overview)

        # Recent Activity section
        if library_info["recent_activity"]:
            recent_content = "## Recent Activity\n\n"
            for activity in library_info["recent_activity"]:
                recent_content += f"- **{activity['title']}** ({activity['created_at']})\n"
                if activity['tags']:
                    recent_content += f"  Tags: {', '.join(activity['tags'])}\n"

            documentation["sections"].append({
                "title": "Recent Activity",
                "content": recent_content.strip()
            })

        # API Reference section
        if include_api_reference:
            api_content = """
## MCP API Reference

### Search Tools
- `search_library(query, limit=10, similarity_threshold=0.7)`: Search library content
- `discover_connections(note_id, connection_threshold=0.6)`: Discover semantic connections
- `get_library_stats()`: Get library statistics

### Note Management
- `create_note(title, content, tags)`: Create a new note
- `update_note(note_id, title, content, tags)`: Update an existing note
- `link_notes(source_note_id, target_note_id)`: Create links between notes

### Workflow Tools
- `start_research_workflow(workflow_type, parameters)`: Start research workflows
- `get_workflow_status(workflow_id)`: Check workflow status

### Export Tools
- `export_library(format, include_content=True)`: Export library data
- `generate_documentation(output_format)`: Generate documentation
            """.strip()

            documentation["sections"].append({
                "title": "API Reference",
                "content": api_content
            })

        # Examples section
        if include_examples:
            examples_content = """
## Usage Examples

### Basic Search
```python
result = await search_library(
    query="machine learning algorithms",
    limit=5,
    similarity_threshold=0.8
)
```

### Note Creation
```python
note = await create_note(
    title="Research Findings",
    content="Detailed analysis of machine learning techniques...",
    tags=["research", "machine-learning", "analysis"]
)
```

### Workflow Execution
```python
workflow = await start_research_workflow(
    workflow_type="research_discovery",
    parameters={"topic": "neural networks"}
)
```
            """.strip()

            documentation["sections"].append({
                "title": "Usage Examples",
                "content": examples_content
            })

        return documentation
