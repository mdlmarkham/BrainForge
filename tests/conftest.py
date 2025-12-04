"""Test configuration and fixtures for BrainForge tests."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock missing dependencies for tests
@pytest.fixture(autouse=True)
def mock_missing_dependencies():
    """Mock missing dependencies that cause import errors."""
    with patch.dict('sys.modules', {
        'spiffworkflow_backend': MagicMock(),
        'spiffworkflow': MagicMock(),
    }):
        yield

@pytest.fixture(autouse=True)
def set_test_environment():
    """Set test environment variables."""
    os.environ['SECRET_KEY'] = 'test-secret-key-for-security-testing-minimum-32-chars'
    os.environ['ENCRYPTION_KEY'] = 'test-encryption-key-for-security-testing-minimum-32-chars'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['DEBUG'] = 'false'
    yield
    # Cleanup if needed

@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    mock_session = MagicMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    return mock_session

@pytest.fixture
def mock_async_session():
    """Create a mock async database session for testing."""
    mock_session = MagicMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    return mock_session

@pytest.fixture
def test_note_data():
    """Create test note data."""
    return {
        "content": "Test note content for unit testing",
        "note_type": "fleeting",
        "created_by": "test@example.com"
    }

@pytest.fixture
def test_agent_run_data():
    """Create test agent run data."""
    return {
        "agent_name": "test_agent",
        "agent_version": "1.0.0",
        "input_parameters": {"test": "data"},
        "status": "pending_review"
    }

@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    mock_service = MagicMock()
    mock_service.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_service.batch_generate_embeddings.return_value = [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.6, 0.7, 0.8, 0.9, 1.0]
    ]
    return mock_service

@pytest.fixture
def mock_search_service():
    """Create a mock search service."""
    mock_service = MagicMock()
    mock_service.semantic_search.return_value = []
    mock_service.hybrid_search.return_value = []
    return mock_service

@pytest.fixture
def mock_auth_service():
    """Create a mock authentication service."""
    mock_service = MagicMock()
    mock_service.create_access_token.return_value = "test-token"
    mock_service.verify_token.return_value = "test-user-id"
    mock_service.hash_password.return_value = "hashed-password"
    mock_service.verify_password.return_value = True
    return mock_service

# Performance testing utilities
@pytest.fixture
def performance_benchmark():
    """Create performance benchmark configuration."""
    return {
        "search_response_time": 500,  # ms
        "embedding_generation_time": 2000,  # ms
        "vector_operation_time": 50,  # ms
        "concurrent_users": 10,
        "dataset_sizes": [1000, 5000, 10000]
    }

# Database fixtures for integration tests
@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL."""
    return os.getenv('DATABASE_URL', 'sqlite:///:memory:')

@pytest.fixture
async def test_database_session(test_database_url):
    """Create a test database session."""
    # This would create an actual database session for integration tests
    # For now, return a mock
    return mock_async_session()

# Test data generation utilities
def generate_test_notes(count=10):
    """Generate test notes for performance testing."""
    notes = []
    for i in range(count):
        notes.append({
            "id": f"note-{i}",
            "content": f"Test note content {i} for performance testing",
            "note_type": "fleeting",
            "created_by": "test@example.com",
            "version": 1
        })
    return notes

def generate_test_embeddings(count=10, dimensions=384):
    """Generate test embeddings for performance testing."""
    embeddings = []
    for i in range(count):
        embedding = [float(j) / dimensions for j in range(dimensions)]
        embeddings.append(embedding)
    return embeddings