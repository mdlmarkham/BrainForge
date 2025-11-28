#!/usr/bin/env python3
"""Database migration CLI for BrainForge using Alembic."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command


def run_migrations() -> int:
    """Run database migrations using Alembic."""
    print("BrainForge Database Migration")
    print("=" * 40)

    # Check if we have database configuration
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        return 1

    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Override the database URL in the config
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # Run migrations
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✓ Migration completed successfully")
        return 0
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return 1


def show_migration_status() -> int:
    """Show current migration status."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        command.current(alembic_cfg)
        return 0
    except Exception as e:
        print(f"Error checking migration status: {e}")
        return 1


def create_migration(message: str) -> int:
    """Create a new migration script."""
    alembic_cfg = Config("alembic.ini")
    
    try:
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print(f"✓ Migration script created: {message}")
        return 0
    except Exception as e:
        print(f"Error creating migration: {e}")
        return 1


def main():
    """Main migration CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BrainForge Database Migration CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run migrations command
    run_parser = subparsers.add_parser("run", help="Run database migrations")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show migration status")
    
    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration description")
    
    args = parser.parse_args()
    
    if args.command == "run":
        return run_migrations()
    elif args.command == "status":
        return show_migration_status()
    elif args.command == "create":
        return create_migration(args.message)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
