"""
Integration tests for API endpoints.
"""

import pytest


@pytest.mark.integration
def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.integration
def test_login_failure(client, test_user):
    """Test failed login with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401


@pytest.mark.integration
def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "roles" in data


@pytest.mark.integration
def test_create_test_script(client, auth_headers):
    """Test creating a test script."""
    response = client.post(
        "/api/v1/tests",
        json={
            "name": "Integration Test Script",
            "description": "Test description",
            "metadata": {"tag": "integration"}
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["success"] is True


@pytest.mark.integration
def test_list_test_scripts(client, auth_headers):
    """Test listing test scripts."""
    # Create a test script first
    client.post(
        "/api/v1/tests",
        json={"name": "Test Script 1"},
        headers=auth_headers
    )
    
    response = client.get("/api/v1/tests", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.integration
def test_create_test_case(client, auth_headers):
    """Test creating a test case."""
    # Create test script first
    script_response = client.post(
        "/api/v1/tests",
        json={"name": "Parent Script"},
        headers=auth_headers
    )
    script_id = script_response.json()["data"]["id"]
    
    # Create test case
    response = client.post(
        "/api/v1/cases",
        json={
            "test_script_id": script_id,
            "name": "Test Case 1",
            "description": "Case description",
            "variables": {"var1": "value1"}
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["success"] is True


@pytest.mark.integration
def test_list_test_cases(client, auth_headers):
    """Test listing test cases."""
    response = client.get("/api/v1/cases", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.integration
def test_unauthorized_access(client):
    """Test accessing protected endpoint without auth."""
    response = client.get("/api/v1/tests")
    
    assert response.status_code == 403


@pytest.mark.integration
def test_execute_ad_hoc(client, auth_headers):
    """Test ad hoc execution."""
    # Create test script and case
    script_response = client.post(
        "/api/v1/tests",
        json={"name": "Execution Test Script"},
        headers=auth_headers
    )
    script_id = script_response.json()["data"]["id"]
    
    case_response = client.post(
        "/api/v1/cases",
        json={
            "test_script_id": script_id,
            "name": "Execution Test Case"
        },
        headers=auth_headers
    )
    case_id = case_response.json()["data"]["id"]
    
    # Execute ad hoc
    response = client.post(
        "/api/v1/execute",
        json={
            "case_ids": [case_id],
            "run_type": "ad_hoc"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 202
    assert response.json()["success"] is True


@pytest.mark.integration
def test_queue_management(client, auth_headers):
    """Test queue operations."""
    # Create test script and case
    script_response = client.post(
        "/api/v1/tests",
        json={"name": "Queue Test Script"},
        headers=auth_headers
    )
    script_id = script_response.json()["data"]["id"]
    
    case_response = client.post(
        "/api/v1/cases",
        json={
            "test_script_id": script_id,
            "name": "Queue Test Case"
        },
        headers=auth_headers
    )
    case_id = case_response.json()["data"]["id"]
    
    # Add to queue
    response = client.post(
        "/api/v1/queue",
        json={"case_ids": [case_id]},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    
    # Get queue
    response = client.get("/api/v1/queue", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Remove from queue
    response = client.delete(f"/api/v1/queue/{case_id}", headers=auth_headers)
    assert response.status_code == 204
