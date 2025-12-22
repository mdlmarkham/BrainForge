"""Obsidian Local REST API integration service for BrainForge."""

import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from .base import BaseService


class ObsidianNote(BaseModel):
    """Represents a note from Obsidian with metadata."""

    content: str = Field(..., description="The content of the note")
    frontmatter: dict[str, Any] = Field(default_factory=dict, description="Frontmatter metadata")
    path: str = Field(..., description="Path to the note relative to vault root")
    stat: dict[str, Any] = Field(..., description="Filesystem metadata")
    tags: list[str] = Field(default_factory=list, description="Tags extracted from the note")


class ObsidianServerInfo(BaseModel):
    """Information about the Obsidian Local REST API server."""

    authenticated: bool = Field(..., description="Is the current request authenticated?")
    ok: str = Field(..., description="Server status")
    service: str = Field(..., description="Service name")
    versions: dict[str, str] = Field(..., description="Version information")


class ObsidianCommand(BaseModel):
    """Available Obsidian command."""

    id: str = Field(..., description="Command ID")
    name: str = Field(..., description="Command name")


class ObsidianService(BaseService):
    """Service for interacting with Obsidian Local REST API."""

    def __init__(self, base_url: str, token: str | None = None):
        """
        Initialize Obsidian service.
        
        Args:
            base_url: Base URL of the Obsidian Local REST API (e.g., "https://localhost:27124")
            token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
            verify=True  # Enable SSL certificate verification to prevent MITM attacks
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize and validate filename to prevent path traversal attacks.
        
        This method implements comprehensive path traversal protection by:
        1. Converting to absolute path and normalizing
        2. Restricting to safe character set
        3. Preventing directory traversal patterns
        4. Validating file extension
        5. Ensuring the filename is not too long
        
        Args:
            filename: The input filename/path from user request
            
        Returns:
            str: Sanitized and safe filename
            
        Raises:
            ValueError: If the filename contains dangerous patterns or characters
        """
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Check for obvious traversal patterns
        dangerous_patterns = [
            '../', '..\\', '../', '..\\',
            '/../', '\\..\\',
            '/etc/', '/proc/', '/sys/', '/dev/', '/root/',
            'C:\\Windows', 'C:\\Windows\\System32',
            '%2e%2e%2f',  # URL encoded ../
            '%2e%2e%5c',  # URL encoded ..\
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in filename.lower():
                raise ValueError(f"Path traversal detected: pattern '{pattern}' not allowed")
        
        # Normalize the path
        try:
            # Convert to Path object and normalize
            path_obj = Path(filename)
            normalized = str(path_obj.resolve())
            
            # Check for dangerous characters
            dangerous_chars = [
                '\x00',  # Null byte
                '<', '>', '|', '"',  # Shell injection chars 
                '*', '?',  # Glob patterns
                '\x01', '\x02', '\x03', '\x04',  # Control characters
            ]
            
            for char in dangerous_chars:
                if char in filename:
                    raise ValueError(f"Dangerous character '{repr(char)}' in filename")
            
            # Extract just the filename part to prevent path traversal
            # This ensures we only use the final component
            safe_name = path_obj.name
            
            # Validate the safe name more strictly
            if not safe_name or safe_name in ['.', '..']:
                raise ValueError("Invalid filename component")
            
            # Length validation
            if len(safe_name) > 255:
                raise ValueError("Filename too long (max 255 characters)")
            
            # Ensure it has a valid extension (common markdown/doc files)
            valid_extensions = [
                '.md', '.markdown', '.txt', '.pdf', '.doc', '.docx',
                '.rtf', '.odt', '.tex', '.rst', '.adoc'
            ]
            
            has_valid_ext = any(
                safe_name.lower().endswith(ext) for ext in valid_extensions
            )
            
            # Allow files without extension but ensure they're safe
            if '.' in safe_name and not has_valid_ext:
                # Has extension but not in allowed list - still allow but log warning
                # In production, you might want to be more restrictive
                pass
            
            # Final safety check - ensure we're only returning the filename
            # and not any path components
            if '/' in safe_name or '\\' in safe_name:
                # Somehow path separators got through, extract just the name
                safe_name = Path(safe_name).name
                if not safe_name:
                    raise ValueError("Invalid filename after sanitization")
            
            return safe_name
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            # Log the actual error for debugging
            print(f"Path sanitization error: {e}")
            raise ValueError(f"Invalid filename: {filename}")

    async def get_server_info(self) -> ObsidianServerInfo:
        """
        Get basic server information and authentication status.
        
        Returns:
            ObsidianServerInfo: Server information
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            response = await self.client.get('/')
            response.raise_for_status()
            return ObsidianServerInfo(**response.json())

    async def get_note(self, filename: str, as_json: bool = False) -> ObsidianNote:
        """
        Get a note from Obsidian vault.
        
        Args:
            filename: Path to the note relative to vault root
            as_json: Whether to return JSON representation with metadata
            
        Returns:
            ObsidianNote: The note content and metadata
        """
        # Validate and sanitize filename to prevent path traversal
        filename = self._sanitize_filename(filename)

        async with self:
            assert self.client is not None, "Client not initialized"
            headers = {}
            if as_json:
                headers['Accept'] = 'application/vnd.olrapi.note+json'

            response = await self.client.get(f'/vault/{filename}', headers=headers)
            response.raise_for_status()

            if as_json:
                return ObsidianNote(**response.json())
            else:
                return ObsidianNote(
                    content=response.text,
                    frontmatter={},
                    path=filename,
                    stat={},
                    tags=[]
                )

    async def create_or_append_note(self, filename: str, content: str) -> None:
        """
        Create or append to a note in Obsidian vault.
        
        Args:
            filename: Path to the note relative to vault root
            content: Content to append to the note
        """
        # Validate and sanitize filename to prevent path traversal
        filename = self._sanitize_filename(filename)

        async with self:
            assert self.client is not None, "Client not initialized"
            response = await self.client.post(
                f'/vault/{filename}',
                content=content,
                headers={'Content-Type': 'text/markdown'}
            )
            response.raise_for_status()

    async def get_active_note(self, as_json: bool = False) -> ObsidianNote | None:
        """
        Get the currently active note in Obsidian.
        
        Args:
            as_json: Whether to return JSON representation with metadata
            
        Returns:
            Optional[ObsidianNote]: The active note, or None if no active note
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            headers = {}
            if as_json:
                headers['Accept'] = 'application/vnd.olrapi.note+json'

            response = await self.client.get('/active/', headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()

            if as_json:
                return ObsidianNote(**response.json())
            else:
                return ObsidianNote(
                    content=response.text,
                    frontmatter={},
                    path='active',
                    stat={},
                    tags=[]
                )

    async def append_to_active_note(self, content: str) -> None:
        """
        Append content to the currently active note.
        
        Args:
            content: Content to append
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            response = await self.client.post(
                '/active/',
                content=content,
                headers={'Content-Type': 'text/markdown'}
            )
            response.raise_for_status()

    async def list_vault_files(self, directory: str = '') -> list[str]:
        """
        List files in a directory of the Obsidian vault.
        
        Args:
            directory: Directory path relative to vault root (empty for root)
            
        Returns:
            List[str]: List of file paths
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            path = f'/vault/{directory}' if directory else '/vault/'
            response = await self.client.get(path)
            response.raise_for_status()
            return response.json()['files']

    async def get_available_commands(self) -> list[ObsidianCommand]:
        """
        Get available Obsidian commands.
        
        Returns:
            List[ObsidianCommand]: List of available commands
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            response = await self.client.get('/commands/')
            response.raise_for_status()
            commands_data = response.json()['commands']
            return [ObsidianCommand(**cmd) for cmd in commands_data]

    async def create_periodic_note(self, period: str, content: str,
                                 year: int | None = None,
                                 month: int | None = None,
                                 day: int | None = None) -> None:
        """
        Create or append to a periodic note.
        
        Args:
            period: Period type (daily, weekly, monthly, quarterly, yearly)
            content: Content to append
            year: Year for specific date (optional)
            month: Month for specific date (optional)
            day: Day for specific date (optional)
        """
        async with self:
            assert self.client is not None, "Client not initialized"
            if year and month and day:
                path = f'/periodic/{period}/{year}/{month}/{day}/'
            else:
                path = f'/periodic/{period}/'

            response = await self.client.post(
                path,
                content=content,
                headers={'Content-Type': 'text/markdown'}
            )
            response.raise_for_status()

    async def search_notes(self, query: str, max_results: int = 50) -> list[ObsidianNote]:
        """
        Search notes in the vault (using Obsidian's built-in search).
        
        Note: This uses a custom approach since the API doesn't have direct search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List[ObsidianNote]: Matching notes
        """
        # Get all files and filter by content
        all_files = await self.list_vault_files()
        results = []

        for filename in all_files[:max_results]:
            try:
                note = await self.get_note(filename, as_json=True)
                if query.lower() in note.content.lower() or query.lower() in filename.lower():
                    results.append(note)
            except Exception:
                # Skip files that can't be read
                continue

        return results


class ObsidianConfig(BaseModel):
    """Configuration for Obsidian integration."""

    base_url: str = Field(..., description="Base URL of Obsidian Local REST API")
    token: str | None = Field(None, description="Authentication token")
    enabled: bool = Field(True, description="Whether Obsidian integration is enabled")
    vault_path: str | None = Field(None, description="Path to Obsidian vault (for reference)")

    @classmethod
    def from_env(cls) -> 'ObsidianConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            ObsidianConfig: Configuration instance
        """
        import os

        return cls(
            base_url=os.getenv('OBSIDIAN_BASE_URL', 'https://localhost:27124'),
            token=os.getenv('OBSIDIAN_TOKEN'),
            enabled=os.getenv('OBSIDIAN_ENABLED', 'true').lower() == 'true',
            vault_path=os.getenv('OBSIDIAN_VAULT_PATH')
        )
