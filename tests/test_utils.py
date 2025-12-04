"""Test utilities and helpers for BrainForge tests."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.models.note import Note, NoteCreate, NoteType
from src.models.user import UserResponse, UserCreate


class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def generate_note(
        content: str = "Test note content",
        note_type: NoteType = NoteType.FLEETING,
        created_by: str = "test@example.com",
        is_ai_generated: bool = False,
        ai_justification: Optional[str] = None
    ) -> Note:
        """Generate a test note."""
        return Note(
            id=uuid4(),
            content=content,
            note_type=note_type,
            created_by=created_by,
            is_ai_generated=is_ai_generated,
            ai_justification=ai_justification,
            version=1
        )
    
    @staticmethod
    def generate_note_create(
        content: str = "Test note content",
        note_type: NoteType = NoteType.FLEETING,
        created_by: str = "test@example.com",
        is_ai_generated: bool = False,
        ai_justification: Optional[str] = None
    ) -> NoteCreate:
        """Generate test note creation data."""
        return NoteCreate(
            content=content,
            note_type=note_type,
            created_by=created_by,
            is_ai_generated=is_ai_generated,
            ai_justification=ai_justification
        )
    
    @staticmethod
    def generate_user(
        username: str = "testuser",
        email: str = "test@example.com",
        hashed_password: str = "hashed_password"
    ) -> UserResponse:
        """Generate a test user."""
        return UserResponse(
            id=uuid4(),
            username=username,
            email=email,
            is_active=True,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
    
    @staticmethod
    def generate_user_create(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "TestPassword123"
    ) -> UserCreate:
        """Generate test user creation data."""
        return UserCreate(
            username=username,
            email=email,
            password=password
        )
    
    @staticmethod
    def generate_notes(count: int = 10, prefix: str = "Test note") -> List[Note]:
        """Generate multiple test notes."""
        return [
            TestDataGenerator.generate_note(
                content=f"{prefix} {i} about artificial intelligence",
                note_type=NoteType.PERMANENT if i % 2 == 0 else NoteType.FLEETING,
                created_by=f"user{i}@example.com"
            )
            for i in range(count)
        ]
    
    @staticmethod
    def generate_embeddings(count: int = 10, dimensions: int = 384) -> List[List[float]]:
        """Generate test embeddings."""
        return [
            [float(j) / dimensions for j in range(dimensions)]
            for i in range(count)
        ]


class PerformanceBenchmark:
    """Utility class for performance benchmarking."""
    
    @staticmethod
    def measure_time(func, *args, **kwargs) -> float:
        """Measure execution time of a function in milliseconds."""
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    @staticmethod
    async def measure_async_time(async_func, *args, **kwargs) -> float:
        """Measure execution time of an async function in milliseconds."""
        start_time = time.time()
        await async_func(*args, **kwargs)
        end_time = time.time()
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    @staticmethod
    def benchmark_concurrent_operations(operations: List, max_concurrent: int = 10) -> Dict[str, Any]:
        """Benchmark concurrent operations."""
        results = {
            "total_operations": len(operations),
            "max_concurrent": max_concurrent,
            "execution_times": [],
            "success_count": 0,
            "error_count": 0
        }
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_operation(operation):
            async with semaphore:
                try:
                    start_time = time.time()
                    if asyncio.iscoroutinefunction(operation):
                        result = await operation()
                    else:
                        result = operation()
                    end_time = time.time()
                    
                    execution_time = (end_time - start_time) * 1000
                    results["execution_times"].append(execution_time)
                    results["success_count"] += 1
                    return result
                except Exception as e:
                    results["error_count"] += 1
                    return e
        
        # Run operations concurrently
        loop = asyncio.get_event_loop()
        tasks = [run_operation(op) for op in operations]
        results["results"] = loop.run_until_complete(asyncio.gather(*tasks))
        
        # Calculate statistics
        if results["execution_times"]:
            results["avg_time"] = sum(results["execution_times"]) / len(results["execution_times"])
            results["min_time"] = min(results["execution_times"])
            results["max_time"] = max(results["execution_times"])
            results["total_time"] = sum(results["execution_times"])
        
        return results


class MockServiceBuilder:
    """Utility class for building mock services."""
    
    @staticmethod
    def create_mock_note_service(notes: Optional[List[Note]] = None) -> Any:
        """Create a mock note service."""
        from unittest.mock import MagicMock
        
        mock_service = MagicMock()
        
        if notes:
            # Create a mapping of note IDs to notes
            note_dict = {str(note.id): note for note in notes}
            mock_service.get_by_id.side_effect = lambda note_id: note_dict.get(str(note_id))
            mock_service.list.return_value = {"notes": notes, "total": len(notes)}
        else:
            mock_service.get_by_id.return_value = None
            mock_service.list.return_value = {"notes": [], "total": 0}
        
        mock_service.create.return_value = TestDataGenerator.generate_note()
        mock_service.update.return_value = TestDataGenerator.generate_note()
        mock_service.delete.return_value = True
        
        return mock_service
    
    @staticmethod
    def create_mock_embedding_service(dimensions: int = 384) -> Any:
        """Create a mock embedding service."""
        from unittest.mock import MagicMock
        
        mock_service = MagicMock()
        mock_service.generate_embedding.return_value = [0.1] * dimensions
        mock_service.batch_generate_embeddings.return_value = [[0.1] * dimensions] * 5
        mock_service.get_model_info.return_value = {
            "name": "text-embedding-3-small",
            "version": "1.0.0",
            "dimensions": dimensions
        }
        
        return mock_service
    
    @staticmethod
    def create_mock_vector_store() -> Any:
        """Create a mock vector store."""
        from unittest.mock import MagicMock
        
        mock_store = MagicMock()
        mock_store.store_embedding.return_value = str(uuid4())
        mock_store.search_similar.return_value = [
            {"note_id": str(uuid4()), "similarity": 0.85}
        ]
        mock_store.get_embedding.return_value = [0.1] * 384
        
        return mock_store
    
    @staticmethod
    def create_mock_search_service() -> Any:
        """Create a mock search service."""
        from unittest.mock import MagicMock
        
        mock_service = MagicMock()
        mock_service.semantic_search.return_value = []
        mock_service.hybrid_search.return_value = []
        mock_service.index_note.return_value = None
        mock_service.update_note_index.return_value = None
        mock_service.remove_note_from_index.return_value = None
        
        return mock_service


class DatabaseTestUtils:
    """Utilities for database testing."""
    
    @staticmethod
    def create_test_database_url() -> str:
        """Create a test database URL."""
        import os
        return os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
    
    @staticmethod
    async def create_test_tables(engine):
        """Create test database tables."""
        from src.models.orm.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    @staticmethod
    async def drop_test_tables(engine):
        """Drop test database tables."""
        from src.models.orm.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


class AssertionHelpers:
    """Helper methods for complex assertions."""
    
    @staticmethod
    def assert_note_structure(note: Note) -> None:
        """Assert that a note has the correct structure."""
        assert hasattr(note, 'id')
        assert hasattr(note, 'content')
        assert hasattr(note, 'note_type')
        assert hasattr(note, 'created_by')
        assert hasattr(note, 'version')
        assert note.content.strip() != "", "Note content cannot be empty"
        assert note.note_type in NoteType, f"Invalid note type: {note.note_type}"
    
    @staticmethod
    def assert_search_results_structure(results: List[Dict]) -> None:
        """Assert that search results have the correct structure."""
        for result in results:
            assert 'note_id' in result, "Search result missing note_id"
            assert 'similarity' in result, "Search result missing similarity"
            assert 0 <= result['similarity'] <= 1.0, f"Invalid similarity score: {result['similarity']}"
    
    @staticmethod
    def assert_performance_within_threshold(actual_time: float, threshold: float, operation: str) -> None:
        """Assert that performance is within threshold."""
        assert actual_time <= threshold, (
            f"{operation} took {actual_time:.2f}ms, exceeding threshold of {threshold}ms"
        )
    
    @staticmethod
    def assert_error_response(response, expected_status: int, expected_error: str = None) -> None:
        """Assert that an error response has the correct structure."""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}"
        )
        if expected_error:
            response_data = response.json()
            assert 'detail' in response_data, "Error response missing detail"
            if expected_error in response_data['detail']:
                assert True
            else:
                # Check if error message contains the expected error
                error_message = str(response_data['detail']).lower()
                assert expected_error.lower() in error_message, (
                    f"Expected error '{expected_error}' not found in response: {response_data['detail']}"
                )


class TestConfiguration:
    """Test configuration utilities."""
    
    @staticmethod
    def setup_test_environment():
        """Set up test environment variables."""
        import os
        os.environ['SECRET_KEY'] = 'test-secret-key-for-security-testing-minimum-32-chars'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['DEBUG'] = 'false'
    
    @staticmethod
    def cleanup_test_environment():
        """Clean up test environment variables."""
        import os
        for key in ['SECRET_KEY', 'DATABASE_URL', 'LOG_LEVEL', 'DEBUG']:
            if key in os.environ and key.startswith('test_'):
                del os.environ[key]


# Common test fixtures that can be imported
test_note = TestDataGenerator.generate_note()
test_note_create = TestDataGenerator.generate_note_create()
test_user = TestDataGenerator.generate_user()
test_user_create = TestDataGenerator.generate_user_create()
test_notes = TestDataGenerator.generate_notes(5)
test_embeddings = TestDataGenerator.generate_embeddings(5)