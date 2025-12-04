#!/usr/bin/env python3
"""
Database Connection Test Script for BrainForge
Tests PostgreSQL connection using the existing SQLAlchemyService
"""

import asyncio
import time
import os
from datetime import datetime
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path to import BrainForge modules
import sys
sys.path.insert(0, 'src')

from src.services.sqlalchemy_service import SQLAlchemyService
from src.models.note import Note  # Using Note model as a sample model for testing


async def test_database_connection():
    """Test database connection using SQLAlchemyService"""
    
    print("BrainForge Database Connection Test")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Please ensure .env file contains DATABASE_URL")
        return False
    
    # Replace postgresql:// with postgresql+asyncpg:// for async operations
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    print(f"Database URL: {database_url.split('@')[0]}@[hidden]")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    try:
        # Initialize SQLAlchemyService with a sample model
        start_time = time.time()
        service = SQLAlchemyService(database_url, Note, Note)
        connection_time = time.time() - start_time
        
        print(f"SQLAlchemyService initialized in {connection_time:.3f} seconds")
        
        # Test connection by executing a simple query
        print("Testing database connection...")
        
        async with service.async_session() as session:
            start_time = time.time()
            
            # Execute simple SELECT 1 query
            result = await session.execute(text("SELECT 1"))
            query_result = result.scalar()
            
            query_time = time.time() - start_time
            
            if query_result == 1:
                print(f"Connection successful! Query executed in {query_time:.3f} seconds")
                print(f"Performance indicators:")
                print(f"   - Service initialization: {connection_time:.3f}s")
                print(f"   - Query execution: {query_time:.3f}s")
                print(f"   - Total test time: {connection_time + query_time:.3f}s")
                
                # Test database version
                version_result = await session.execute(text("SELECT version()"))
                db_version = version_result.scalar()
                print(f"Database version: {db_version.split(',')[0]}")
                
                return True
            else:
                print(f"Unexpected query result: {query_result}")
                return False
                
    except Exception as e:
        print(f"Connection failed with error: {str(e)}")
        print("Troubleshooting suggestions:")
        print("   - Check if PostgreSQL server is running")
        print("   - Verify DATABASE_URL format and credentials")
        print("   - Ensure network connectivity to database host")
        print("   - Check if database 'brainforge' exists")
        return False


async def test_advanced_operations():
    """Test more advanced database operations"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return
    
    # Replace postgresql:// with postgresql+asyncpg:// for async operations
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    try:
        service = SQLAlchemyService(database_url, Note, Note)
        
        async with service.async_session() as session:
            # Test transaction capabilities
            print("\nTesting transaction capabilities...")
            
            # Test if we can begin and commit a transaction
            await session.begin()
            
            # Test if we can rollback
            await session.rollback()
            
            print("Transaction capabilities working correctly")
            
            # Test if database has required tables
            print("\nChecking database schema...")
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(tables)} tables in database")
            if tables:
                print(f"   - Tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
            
    except Exception as e:
        print(f"Advanced operations test failed: {str(e)}")


async def main():
    """Main test function"""
    
    # Test basic connection
    basic_success = await test_database_connection()
    
    if basic_success:
        # Test advanced operations if basic connection works
        await test_advanced_operations()
        
        print("\nDatabase connection test completed successfully!")
        print("Next steps:")
        print("   - Run database migrations: alembic upgrade head")
        print("   - Test API endpoints: cd src; uvicorn api.main:app --reload")
        print("   - Run full test suite: cd src; pytest")
    else:
        print("\nDatabase connection test failed!")
        print("Please fix the connection issues before proceeding")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())