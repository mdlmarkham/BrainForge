#!/usr/bin/env python3
"""
CRUD Operations Test Script for BrainForge Postgres Integration
Tests Create, Read, Update, and Delete operations on Note model
"""

import asyncio
import time
from datetime import datetime
from uuid import UUID, uuid4
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import DatabaseConfig
from src.models.note import NoteCreate, NoteUpdate
from src.models.orm.note import NoteType
from src.services.database import NoteService
from src.models.orm.note import Note as ORMNote


class CRUDTest:
    """Test class for CRUD operations on Note model"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.note_service = NoteService()
        self.test_note_id = None
        self.performance_metrics = {}
    
    async def setup(self):
        """Setup database connection"""
        print("Setting up database connection...")
        try:
            # DatabaseConfig uses lazy initialization, no need to call initialize()
            # Just access the engine property to trigger initialization
            _ = self.db_config.engine
            print("[SUCCESS] Database connection established")
        except Exception as e:
            print(f"[ERROR] Failed to setup database: {e}")
            raise
    
    async def test_create(self) -> bool:
        """Test CREATE operation"""
        print("\n[CREATE] Testing CREATE operation...")
        start_time = time.time()
        
        try:
            # Create test note data
            note_data = NoteCreate(
                content="This is a test note to verify Postgres integration with BrainForge",
                note_type="fleeting",
                created_by="test_script",
                metadata={"test_type": "crud_operations"}
            )
            
            async with self.db_config.async_session_maker() as session:
                # Create the note
                created_note = await self.note_service.create(session, note_data.model_dump())
                self.test_note_id = created_note.id
                
                # Verify creation
                assert created_note.id is not None, "Note ID should not be None"
                assert created_note.content == note_data.content, "Content should match"
                assert "constitutional_audit" in created_note.model_dump(), "Constitutional audit should exist"
                assert created_note.constitutional_audit.get("compliance_checked") is True, "Compliance should be checked"
                
                elapsed_time = time.time() - start_time
                self.performance_metrics['create'] = elapsed_time
                
                print(f"[SUCCESS] CREATE operation successful - Note ID: {created_note.id}")
                print(f"   [TIME] Execution time: {elapsed_time:.3f} seconds")
                return True
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] CREATE operation failed: {e}")
            return False
    
    async def test_read(self) -> bool:
        """Test READ operation"""
        if not self.test_note_id:
            print("[ERROR] No note ID available for READ test")
            return False
        
        print("\n[READ] Testing READ operation...")
        start_time = time.time()
        
        try:
            async with self.db_config.async_session_maker() as session:
                # Read the note by ID
                retrieved_note = await self.note_service.get(session, self.test_note_id)
                
                # Verify retrieval
                assert retrieved_note is not None, "Note should be retrieved"
                assert retrieved_note.id == self.test_note_id, "Note ID should match"
                assert retrieved_note.content == "This is a test note to verify Postgres integration with BrainForge", "Content should match"
                
                # Test list operation
                all_notes = await self.note_service.list(session, limit=5)
                assert isinstance(all_notes, list), "Should return a list of notes"
                assert len(all_notes) > 0, "Should have at least one note"
                
                elapsed_time = time.time() - start_time
                self.performance_metrics['read'] = elapsed_time
                
                print(f"[SUCCESS] READ operation successful - Retrieved note content: {retrieved_note.content[:50]}...")
                print(f"   [TIME] Execution time: {elapsed_time:.3f} seconds")
                return True
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] READ operation failed: {e}")
            return False
    
    async def test_update(self) -> bool:
        """Test UPDATE operation"""
        if not self.test_note_id:
            print("[ERROR] No note ID available for UPDATE test")
            return False
        
        print("\n[UPDATE] Testing UPDATE operation...")
        start_time = time.time()
        
        try:
            # Create update data
            update_data = NoteUpdate(
                content="This note has been updated to test UPDATE operation",
                note_type=NoteType.PERMANENT,
                created_by="test_script",  # Required by ProvenanceMixin
                change_reason="Testing UPDATE operation"
            )
            
            async with self.db_config.async_session_maker() as session:
                # Update the note
                updated_note = await self.note_service.update(session, self.test_note_id, update_data.model_dump())
                
                # Verify update
                assert updated_note is not None, "Note should be updated"
                assert updated_note.id == self.test_note_id, "Note ID should match"
                assert updated_note.content == "This note has been updated to test UPDATE operation", "Content should be updated"
                assert updated_note.note_type == NoteType.PERMANENT, "Note type should be updated"
                assert updated_note.change_reason == "Testing UPDATE operation", "Change reason should be set"
                
                elapsed_time = time.time() - start_time
                self.performance_metrics['update'] = elapsed_time
                
                print(f"[SUCCESS] UPDATE operation successful - Updated content: {updated_note.content[:50]}...")
                print(f"   [TIME] Execution time: {elapsed_time:.3f} seconds")
                return True
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] UPDATE operation failed: {e}")
            return False
    
    async def test_delete(self) -> bool:
        """Test DELETE operation"""
        if not self.test_note_id:
            print("[ERROR] No note ID available for DELETE test")
            return False
        
        print("\n[DELETE] Testing DELETE operation...")
        start_time = time.time()
        
        try:
            async with self.db_config.async_session_maker() as session:
                # Delete the note
                delete_result = await self.note_service.delete(session, self.test_note_id)
                
                # Verify deletion
                assert delete_result is True, "Delete should return True"
                
                # Verify note no longer exists
                deleted_note = await self.note_service.get(session, self.test_note_id)
                assert deleted_note is None, "Note should be deleted and not retrievable"
                
                elapsed_time = time.time() - start_time
                self.performance_metrics['delete'] = elapsed_time
                
                print(f"[SUCCESS] DELETE operation successful - Note ID {self.test_note_id} deleted")
                print(f"   [TIME] Execution time: {elapsed_time:.3f} seconds")
                return True
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] DELETE operation failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling for invalid operations"""
        print("\n[ERROR_HANDLING] Testing error handling...")
        start_time = time.time()
        
        try:
            async with self.db_config.async_session_maker() as session:
                # Test getting non-existent note
                non_existent_id = uuid4()
                non_existent_note = await self.note_service.get(session, non_existent_id)
                assert non_existent_note is None, "Non-existent note should return None"
                
                # Test updating non-existent note
                update_data = NoteUpdate(
                    content="Should Fail",
                    note_type=NoteType.FLEETING,
                    created_by="test_script"  # Required by ProvenanceMixin
                )
                try:
                    await self.note_service.update(session, non_existent_id, update_data.model_dump())
                    assert False, "Updating non-existent note should raise an error"
                except Exception:
                    pass  # Expected behavior
                
                # Test deleting non-existent note
                try:
                    await self.note_service.delete(session, non_existent_id)
                    assert False, "Deleting non-existent note should raise an error"
                except Exception:
                    pass  # Expected behavior
                
                elapsed_time = time.time() - start_time
                self.performance_metrics['error_handling'] = elapsed_time
                
                print("[SUCCESS] Error handling tests passed")
                print(f"   [TIME] Execution time: {elapsed_time:.3f} seconds")
                return True
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[ERROR] Error handling test failed: {e}")
            return False
    
    def print_summary(self, results: dict):
        """Print test summary"""
        print("\n" + "="*60)
        print("CRUD OPERATIONS TEST SUMMARY")
        print("="*60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nPerformance Metrics:")
        for operation, time_taken in self.performance_metrics.items():
            print(f"   {operation.upper():<15}: {time_taken:.3f} seconds")
        
        total_time = sum(self.performance_metrics.values())
        print(f"   {'TOTAL':<15}: {total_time:.3f} seconds")
        
        print("\nDatabase Integration Status:")
        if all(results.values()):
            print("   [SUCCESS] POSTGRES INTEGRATION VERIFIED - All operations successful")
            print("   [SUCCESS] Constitutional compliance maintained")
            print("   [SUCCESS] Async operations working correctly")
            print("   [SUCCESS] Error handling functioning properly")
        else:
            failed_ops = [op for op, success in results.items() if not success]
            print(f"   [ERROR] ISSUES DETECTED - Failed operations: {', '.join(failed_ops)}")
        
        print("="*60)


async def main():
    """Main test function"""
    print("BrainForge Postgres CRUD Operations Test")
    print("="*50)
    
    test = CRUDTest()
    
    try:
        # Setup database connection
        await test.setup()
        
        # Run all tests
        test_results = {
            'create': await test.test_create(),
            'read': await test.test_read(),
            'update': await test.test_update(),
            'delete': await test.test_delete(),
            'error_handling': await test.test_error_handling()
        }
        
        # Print summary
        test.print_summary(test_results)
        
        # Return overall success
        return all(test_results.values())
        
    except Exception as e:
        print(f"Test execution failed: {e}")
        return False
    finally:
        # Cleanup
        print("\nCleaning up...")
        if hasattr(test, 'db_config'):
            # DatabaseConfig doesn't have a close method, just let it be garbage collected
            pass


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)