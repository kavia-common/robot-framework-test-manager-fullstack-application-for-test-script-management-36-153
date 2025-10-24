"""
Unit tests for test scripts router.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.main import app

client = TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication dependency"""
    with patch("src.core.security.get_current_user") as mock:
        mock.return_value = {"sub": "test-user-id", "username": "testuser", "roles": ["admin"]}
        yield mock


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_api_health_check():
    """Test API health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


# Additional test cases would be added here for full coverage
# Example structure:
# - test_create_test_script()
# - test_list_test_scripts()
# - test_get_test_script()
# - test_update_test_script()
# - test_delete_test_script()
