import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Test configuration
@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary test data directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def test_docs_dir(test_data_dir):
    """Create test docs directory"""
    docs_dir = os.path.join(test_data_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    return docs_dir

@pytest.fixture(scope="session")
def test_index_dir(test_data_dir):
    """Create test index directory"""
    index_dir = os.path.join(test_data_dir, "index")
    os.makedirs(index_dir, exist_ok=True)
    return index_dir

@pytest.fixture(scope="session")
def test_db_path(test_data_dir):
    """Create test database path"""
    return os.path.join(test_data_dir, "test.db")

@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for testing"""
    monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deployment")

