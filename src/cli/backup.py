"""Backup and recovery CLI for BrainForge production deployment."""

import asyncio
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import asyncpg
from sqlalchemy import text

from src.config.database import db_config

logger = logging.getLogger(__name__)


class BackupService:
    """Service for automated database backup and recovery."""
    
    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize backup service.
        
        Args:
            backup_dir: Backup directory. If None, uses BACKUP_DIR env var.
        """
        self.backup_dir = Path(backup_dir or os.getenv("BACKUP_DIR", "/backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        self.compression_enabled = os.getenv("BACKUP_COMPRESSION", "true").lower() == "true"
    
    async def create_backup(self) -> str:
        """Create a database backup.
        
        Returns:
            Path to the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"brainforge_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Get database connection parameters from URL
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is required")
            
            # Parse connection parameters
            conn_params = self._parse_db_url(db_url)
            
            # Create backup using pg_dump
            cmd = [
                "pg_dump",
                f"--host={conn_params['host']}",
                f"--port={conn_params['port']}",
                f"--username={conn_params['user']}",
                f"--dbname={conn_params['database']}",
                "--format=custom",  # Custom format for better compression
                "--verbose",
                f"--file={backup_path}",
            ]
            
            # Set password in environment for pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = conn_params["password"]
            
            # Execute backup command
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Backup failed: {result.stderr}")
            
            logger.info(f"Backup created successfully: {backup_path}")
            
            # Compress backup if enabled
            if self.compression_enabled:
                backup_path = await self._compress_backup(backup_path)
            
            # Clean up old backups
            await self._cleanup_old_backups()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            # Clean up failed backup file if it exists
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    async def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            # Decompress backup if compressed
            if backup_path.endswith('.gz'):
                backup_path = await self._decompress_backup(backup_path)
            
            # Get database connection parameters
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is required")
            
            conn_params = self._parse_db_url(db_url)
            
            # Drop and recreate database for clean restore
            await self._recreate_database(conn_params)
            
            # Restore backup using pg_restore
            cmd = [
                "pg_restore",
                f"--host={conn_params['host']}",
                f"--port={conn_params['port']}",
                f"--username={conn_params['user']}",
                f"--dbname={conn_params['database']}",
                "--verbose",
                "--clean",  # Clean (drop) database objects before recreation
                "--if-exists",
                backup_path,
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = conn_params["password"]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Restore failed: {result.stderr}")
            
            logger.info(f"Backup restored successfully from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            return False
    
    async def list_backups(self) -> list[dict]:
        """List available backups.
        
        Returns:
            List of backup information
        """
        backups = []
        
        for backup_file in self.backup_dir.glob("brainforge_backup_*.sql*"):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "compressed": backup_file.suffix == '.gz',
            })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup file using gzip.
        
        Args:
            backup_path: Path to uncompressed backup
            
        Returns:
            Path to compressed backup
        """
        compressed_path = backup_path.with_suffix('.sql.gz')
        
        cmd = ["gzip", "-f", str(backup_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Backup compression failed: {result.stderr}")
        
        return compressed_path
    
    async def _decompress_backup(self, backup_path: str) -> str:
        """Decompress backup file.
        
        Args:
            backup_path: Path to compressed backup
            
        Returns:
            Path to decompressed backup
        """
        decompressed_path = backup_path.replace('.gz', '')
        
        cmd = ["gunzip", "-f", backup_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Backup decompression failed: {result.stderr}")
        
        return decompressed_path
    
    async def _cleanup_old_backups(self):
        """Clean up backups older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob("brainforge_backup_*.sql*"):
            if backup_file.stat().st_ctime < cutoff_date.timestamp():
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file.name}")
    
    async def _recreate_database(self, conn_params: dict):
        """Recreate database for clean restore.
        
        Args:
            conn_params: Database connection parameters
        """
        # Connect to postgres database to drop and recreate target database
        conn = await asyncpg.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database="postgres"
        )
        
        try:
            # Terminate existing connections to target database
            await conn.execute(f"""
                SELECT pg_terminate_backend(pid) 
                FROM pg_stat_activity 
                WHERE datname = $1 AND pid <> pg_backend_pid()
            """, conn_params["database"])
            
            # Drop and recreate database
            await conn.execute(f"DROP DATABASE IF EXISTS {conn_params['database']}")
            await conn.execute(f"CREATE DATABASE {conn_params['database']}")
            
        finally:
            await conn.close()
    
    def _parse_db_url(self, db_url: str) -> dict:
        """Parse database URL into connection parameters.
        
        Args:
            db_url: Database URL
            
        Returns:
            Connection parameters dictionary
        """
        # Remove asyncpg prefix if present
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Parse URL components
        parts = db_url.split("://")[1].split("@")
        user_pass = parts[0].split(":")
        host_port_db = parts[1].split("/")
        host_port = host_port_db[0].split(":")
        
        return {
            "user": user_pass[0],
            "password": user_pass[1] if len(user_pass) > 1 else "",
            "host": host_port[0],
            "port": host_port[1] if len(host_port) > 1 else "5432",
            "database": host_port_db[1],
        }


async def main():
    """Main backup CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BrainForge Backup CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create backup command
    create_parser = subparsers.add_parser("create", help="Create a new backup")
    
    # Restore backup command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_path", help="Path to backup file")
    
    # List backups command
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    args = parser.parse_args()
    
    backup_service = BackupService()
    
    try:
        if args.command == "create":
            backup_path = await backup_service.create_backup()
            print(f"Backup created: {backup_path}")
            
        elif args.command == "restore":
            success = await backup_service.restore_backup(args.backup_path)
            if success:
                print("Backup restored successfully")
            else:
                print("Backup restore failed")
                exit(1)
                
        elif args.command == "list":
            backups = await backup_service.list_backups()
            for backup in backups:
                print(f"{backup['filename']} - {backup['size']} bytes - {backup['created']}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Backup operation failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())