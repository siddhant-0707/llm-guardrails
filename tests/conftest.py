"""Pytest configuration and fixtures"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import create_app
from app.config import Settings


@pytest.fixture
def test_settings():
    """Test settings override"""
    return Settings(
        environment="test",
        redis_host="localhost",
        redis_port=6379,
        api_port=8000,
        guardrails_enabled=True,
        pii_redaction_enabled=True,
        content_policy_enabled=True,
        prompt_injection_detection_enabled=True,
    )


@pytest.fixture
def app(test_settings):
    """Create test FastAPI application"""
    with patch("app.main.get_settings", return_value=test_settings):
        app = create_app()
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.incr.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.pipeline.return_value.__enter__.return_value = mock_redis
    mock_redis.pipeline.return_value.__exit__.return_value = None
    return mock_redis


@pytest.fixture
def mock_vector_db():
    """Mock vector database"""
    mock_db = MagicMock()
    mock_db.similarity_search.return_value = []
    mock_db.add_documents.return_value = ["doc1", "doc2"]
    mock_db.exists.return_value = False
    mock_db.delete.return_value = True
    return mock_db


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager"""
    mock_memory = MagicMock()
    mock_memory.add_memory.return_value = "memory_id_123"
    mock_memory.search_memories.return_value = []
    mock_memory.get_all_memories.return_value = []
    mock_memory.delete_memory.return_value = True
    return mock_memory


@pytest.fixture(autouse=True)
def setup_test():
    """Setup test environment"""
    yield
    # Cleanup after tests
    pass

