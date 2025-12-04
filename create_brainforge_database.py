#!/usr/bin/env python3
"""
Database Creation Script for BrainForge
Creates the 'brainforge' database on the PostgreSQL server
"""

import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path to import BrainForge modules
sys.path.insert(0, 'src')

from src.services.sqlalchemy_service import SQLAlchemyService
from src.models.note import Note  # Using Note model as a sample model


async def create_brainforge_database():
    """Create the brainforge database on the PostgreSQL server"""
    
    print("BrainForge Database Creation Script")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Please ensure .env file contains DATABASE_URL")
        return False
    
    # Create a connection URL to the default 'postgres' database
    # Replace the database name in the URL with 'postgres' (default database)
    default_db_url = database_url.replace('/brainforge', '/postgres')
    
    # Replace postgresql:// with postgresql+asyncpg:// for async operations
    if default_db_url.startswith('postgresql://'):
        default_db_url = default_db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    print(f"Server URL: {default_db_url.split('@')[0]}@[hidden]")
    print(f"Target database: brainforge")
    print(f"Operation started at: {datetime.now().isoformat()}")
    
    try:
        # Initialize SQLAlchemyService with the default database
        print("Connecting to default 'postgres' database...")
        service = SQLAlchemyService(default_db_url, Note, Note)
        
        async with service.async_session() as session:
            # Check if brainforge database already exists
            print("Checking if 'brainforge' database exists...")
            result = await session.execute(text("""
                SELECT 1 FROM pg_database WHERE datname = 'brainforge'
            """))
            db_exists = result.scalar() is not None
            
            if db_exists:
                print("Database 'brainforge' already exists")
                return True
            
            # Create the brainforge database
            print("Creating 'brainforge' database...")
            
            # Note: We need to commit the current transaction before creating the database
            await session.commit()
            
            # Execute CREATE DATABASE command
            create_result = await session.execute(text("CREATE DATABASE brainforge"))
            print("Database creation command executed")
            
            # Verify the database was created
            await session.commit()
            
            # Reconnect to check if database was created
            result = await session.execute(text("""
                SELECT 1 FROM pg_database WHERE datname = 'brainforge'
            """))
            db_created = result.scalar() is not None
            
            if db_created:
                print("SUCCESS: Database 'brainforge' created successfully!")
                
                # Test connecting to the new database
                print("Testing connection to new database...")
                brainforge_url = database_url.replace('/postgres', '/brainforge')
                if brainforge_url.startswith('postgresql://'):
                    brainforge_url = brainforge_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
                
                try:
                    brainforge_service = SQLAlchemyService(brainforge_url, Note, Note)
                    async with brainforge_service.async_session() as test_session:
                        test_result = await test_session.execute(text("SELECT 1"))
                        if test_result.scalar() == 1:
                            print("SUCCESS: Connection to 'brainforge' database successful!")
                            return True
                except Exception as e:
                    print(f"⚠️  Connection test failed: {str(e)}")
                    print("Database was created but connection test failed")
                    return True
            else:
                print("ERROR: Database creation verification failed")
                return False
                
    except Exception as e:
        print(f"ERROR: Database creation failed with error: {str(e)}")
        print("Troubleshooting suggestions:")
        print("   - Check if PostgreSQL server is running")
        print("   - Verify user has CREATE DATABASE privileges")
        print("   - Ensure network connectivity to database host")
        return False


async def list_databases():
    """List all databases on the server for verification"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return
    
    # Create a connection URL to the default 'postgres' database
    default_db_url = database_url.replace('/brainforge', '/postgres')
    if default_db_url.startswith('postgresql://'):
        default_db_url = default_db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    try:
        service = SQLAlchemyService(default_db_url, Note, Note)
        
        async with service.async_session() as session:
            result = await session.execute(text("""
                SELECT datname FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname
            """))
            databases = [row[0] for row in result.fetchall()]
            
            print("\n📊 Available databases on server:")
            for db in databases:
                print(f"   - {db}")
            
    except Exception as e:
        print(f"Failed to list databases: {str(e)}")


async def main():
    """Main function to create the database"""
    
    # Create the brainforge database
    success = await create_brainforge_database()
    
    if success:
        # List databases for verification
        await list_databases()
        
        print("\nSUCCESS: Database creation completed successfully!")
        print("Next steps:")
        print("   - Run database migrations: alembic upgrade head")
        print("   - Test the application: cd src; uvicorn api.main:app --reload")
        print("   - Run full test suite: cd src; pytest")
    else:
        print("\nFAILURE: Database creation failed!")
        print("Please fix the issues before proceeding")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())