"""Obsidian Local REST API integration service for BrainForge."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

from .base import BaseService


class ObsidianNote(BaseModel):
    """Represents a note from Obsidian with metadata."""
    
    content: str = Field(..., description="The content of the note")
    frontmatter: Dict[str, Any] = Field(default_factory=dict, description="Frontmatter metadata")
    path: str = Field(..., description="Path to the note relative to vault root")
    stat: Dict[str, Any] = Field(..., description="Filesystem metadata")
    tags: List[str] = Field(default_factory=list, description="Tags extracted from the note")


class ObsidianServerInfo(BaseModel):
    """Information about the Obsidian Local REST API server."""
    
    authenticated: bool = Field(..., description="Is the current request authenticated?")
    ok: str = Field(..., description="Server status")
    service: str = Field(..., description="Service name")
    versions: Dict[str, str] = Field(..., description="Version information")


class ObsidianCommand(BaseModel):
    """Available Obsidian command."""
    
    id: str = Field(..., description="Command ID")
    name: str = Field(..., description="Command name")


class ObsidianService(BaseService):
    """Service for interacting with Obsidian Local REST API."""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        """
        Initialize Obsidian service.
        
        Args:
            base_url: Base URL of the Obsidian Local REST API (e.g., "https://localhost:27124")
            token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            verify=False,  # Obsidian uses self-signed certificates
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
            
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
        async with self:
            assert self.client is not None, "Client not initialized"
            response = await self.client.post(
                f'/vault/{filename}',
                content=content,
                headers={'Content-Type': 'text/markdown'}
            )
            response.raise_for_status()
            
    async def get_active_note(self, as_json: bool = False) -> Optional[ObsidianNote]:
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
            
    async def list_vault_files(self, directory: str = '') -> List[str]:
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
            
    async def get_available_commands(self) -> List[ObsidianCommand]:
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
                                 year: Optional[int] = None,
                                 month: Optional[int] = None,
                                 day: Optional[int] = None) -> None:
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
            
    async def search_notes(self, query: str, max_results: int = 50) -> List[ObsidianNote]:
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
    token: Optional[str] = Field(None, description="Authentication token")
    enabled: bool = Field(True, description="Whether Obsidian integration is enabled")
    vault_path: Optional[str] = Field(None, description="Path to Obsidian vault (for reference)")
    
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