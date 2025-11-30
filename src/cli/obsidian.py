#!/usr/bin/env python3
"""Obsidian integration CLI for BrainForge."""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.obsidian import ObsidianService


async def test_connection(base_url: str, token: str | None = None) -> bool:
    """Test connection to Obsidian Local REST API."""
    service = ObsidianService(base_url=base_url, token=token)

    try:
        info = await service.get_server_info()
        print(f"✓ Connected to Obsidian server: {info.service}")
        print(f"  Status: {info.ok}")
        print(f"  Authentication: {'Authenticated' if info.authenticated else 'Not authenticated'}")
        print(f"  Versions: {info.versions}")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


async def list_vault_files(base_url: str, token: str | None = None, directory: str = '') -> None:
    """List files in Obsidian vault."""
    service = ObsidianService(base_url=base_url, token=token)

    try:
        files = await service.list_vault_files(directory)
        print(f"Files in vault directory '{directory or 'root'}':")
        for file in files:
            print(f"  - {file}")
        print(f"Total files: {len(files)}")
    except Exception as e:
        print(f"Error listing files: {e}")


async def get_note(base_url: str, token: str | None = None, filename: str = '', as_json: bool = False) -> None:
    """Get a note from Obsidian vault."""
    if not filename:
        print("Error: filename is required")
        return

    service = ObsidianService(base_url=base_url, token=token)

    try:
        note = await service.get_note(filename, as_json=as_json)
        print(f"Note: {filename}")
        print(f"Content: {note.content[:200]}...")  # Show first 200 chars
        if as_json and note.frontmatter:
            print(f"Frontmatter: {note.frontmatter}")
    except Exception as e:
        print(f"Error getting note: {e}")


async def get_active_note(base_url: str, token: str | None = None, as_json: bool = False) -> None:
    """Get the currently active note in Obsidian."""
    service = ObsidianService(base_url=base_url, token=token)

    try:
        note = await service.get_active_note(as_json=as_json)
        if note:
            print("Active note found:")
            print(f"Content: {note.content[:200]}...")
            if as_json and note.frontmatter:
                print(f"Frontmatter: {note.frontmatter}")
        else:
            print("No active note found")
    except Exception as e:
        print(f"Error getting active note: {e}")


async def sync_vault(base_url: str, token: str | None = None) -> None:
    """Sync BrainForge database with Obsidian vault."""
    service = ObsidianService(base_url=base_url, token=token)

    try:
        files = await service.list_vault_files()
        print(f"Found {len(files)} files in vault")
        print("Sync functionality to be implemented...")
        # TODO: Implement actual sync logic
    except Exception as e:
        print(f"Error syncing vault: {e}")


def main():
    """Main Obsidian CLI function."""
    import argparse

    parser = argparse.ArgumentParser(description="BrainForge Obsidian Integration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Test connection command
    test_parser = subparsers.add_parser("test", help="Test connection to Obsidian API")
    test_parser.add_argument("--url", default="http://localhost:27124", help="Obsidian API URL")
    test_parser.add_argument("--token", help="Authentication token")

    # List files command
    list_parser = subparsers.add_parser("list", help="List files in Obsidian vault")
    list_parser.add_argument("--url", default="http://localhost:27124", help="Obsidian API URL")
    list_parser.add_argument("--token", help="Authentication token")
    list_parser.add_argument("--directory", default="", help="Directory to list")

    # Get note command
    get_parser = subparsers.add_parser("get", help="Get a note from Obsidian vault")
    get_parser.add_argument("--url", default="http://localhost:27124", help="Obsidian API URL")
    get_parser.add_argument("--token", help="Authentication token")
    get_parser.add_argument("filename", help="Note filename")
    get_parser.add_argument("--json", action="store_true", help="Return JSON format")

    # Get active note command
    active_parser = subparsers.add_parser("active", help="Get active note")
    active_parser.add_argument("--url", default="http://localhost:27124", help="Obsidian API URL")
    active_parser.add_argument("--token", help="Authentication token")
    active_parser.add_argument("--json", action="store_true", help="Return JSON format")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync with Obsidian vault")
    sync_parser.add_argument("--url", default="http://localhost:27124", help="Obsidian API URL")
    sync_parser.add_argument("--token", help="Authentication token")

    args = parser.parse_args()

    # Get base URL and token from environment if not provided
    base_url = args.url if hasattr(args, 'url') else os.getenv("OBSIDIAN_API_URL", "http://localhost:27124")
    token = args.token if hasattr(args, 'token') else os.getenv("OBSIDIAN_API_TOKEN")

    if args.command == "test":
        result = asyncio.run(test_connection(base_url, token))
        return 0 if result else 1
    elif args.command == "list":
        directory = args.directory if hasattr(args, 'directory') else ''
        asyncio.run(list_vault_files(base_url, token, directory))
        return 0
    elif args.command == "get":
        filename = args.filename if hasattr(args, 'filename') else ''
        as_json = args.json if hasattr(args, 'json') else False
        asyncio.run(get_note(base_url, token, filename, as_json))
        return 0
    elif args.command == "active":
        as_json = args.json if hasattr(args, 'json') else False
        asyncio.run(get_active_note(base_url, token, as_json))
        return 0
    elif args.command == "sync":
        asyncio.run(sync_vault(base_url, token))
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
