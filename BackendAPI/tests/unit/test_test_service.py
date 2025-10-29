"""
Unit tests for test script service.
"""

import pytest
from src.services.test_service import test_service
from src.schemas.test_script import TestScriptCreate, TestScriptUpdate


@pytest.mark.unit
def test_create_test_script(db_session, test_user):
    """Test creating a test script."""
    script_data = TestScriptCreate(
        name="My Test Script",
        description="Test description",
        metadata={"tags": ["smoke", "regression"]}
    )
    
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    assert script.name == "My Test Script"
    assert script.description == "Test description"
    assert script.metadata == {"tags": ["smoke", "regression"]}
    assert script.created_by == test_user.id


@pytest.mark.unit
def test_get_test_script(db_session, test_user):
    """Test retrieving a test script."""
    script_data = TestScriptCreate(name="Test Script", description="Description")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    retrieved = test_service.get_test_script(db_session, script.id)
    
    assert retrieved is not None
    assert retrieved.id == script.id
    assert retrieved.name == "Test Script"


@pytest.mark.unit
def test_list_test_scripts(db_session, test_user):
    """Test listing test scripts."""
    for i in range(3):
        script_data = TestScriptCreate(name=f"Test Script {i}")
        test_service.create_test_script(db_session, script_data, test_user.id)
    
    scripts = test_service.list_test_scripts(db_session)
    
    assert len(scripts) == 3


@pytest.mark.unit
def test_update_test_script(db_session, test_user):
    """Test updating a test script."""
    script_data = TestScriptCreate(name="Original Name")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    update_data = TestScriptUpdate(name="Updated Name", description="New description")
    updated = test_service.update_test_script(db_session, script.id, update_data)
    
    assert updated.name == "Updated Name"
    assert updated.description == "New description"


@pytest.mark.unit
def test_delete_test_script(db_session, test_user):
    """Test deleting a test script (soft delete)."""
    script_data = TestScriptCreate(name="To Delete")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    test_service.delete_test_script(db_session, script.id)
    
    # Should not be retrievable after delete
    retrieved = test_service.get_test_script(db_session, script.id)
    assert retrieved is None


@pytest.mark.unit
def test_get_total_count(db_session, test_user):
    """Test getting total count of test scripts."""
    for i in range(5):
        script_data = TestScriptCreate(name=f"Script {i}")
        test_service.create_test_script(db_session, script_data, test_user.id)
    
    count = test_service.get_total_count(db_session)
    assert count == 5
