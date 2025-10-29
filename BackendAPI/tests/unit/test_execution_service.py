"""
Unit tests for execution service.
"""

import pytest
from src.services.execution_service import execution_service
from src.services.test_service import test_service
from src.services.case_service import case_service
from src.schemas.test_script import TestScriptCreate
from src.schemas.test_case import TestCaseCreate
from src.database.models import ExecutionStatus


@pytest.mark.unit
def test_create_run(db_session, test_user):
    """Test creating a run record."""
    # Create test script and case
    script_data = TestScriptCreate(name="Test Script")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    case_data = TestCaseCreate(
        test_script_id=script.id,
        name="Test Case",
        description="Description"
    )
    case = case_service.create_test_case(db_session, case_data, test_user.id)
    
    # Create run
    run = execution_service.create_run(db_session, case.id, test_user.id)
    
    assert run.case_id == case.id
    assert run.status == ExecutionStatus.PENDING
    assert run.triggered_by == test_user.id


@pytest.mark.unit
def test_start_run(db_session, test_user):
    """Test starting a run."""
    # Create test script and case
    script_data = TestScriptCreate(name="Test Script")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    case_data = TestCaseCreate(test_script_id=script.id, name="Test Case")
    case = case_service.create_test_case(db_session, case_data, test_user.id)
    
    # Create and start run
    run = execution_service.create_run(db_session, case.id, test_user.id)
    execution_service.start_run(db_session, run.run_id)
    
    # Verify status changed
    db_session.refresh(run)
    assert run.status == ExecutionStatus.RUNNING
    assert run.started_at is not None


@pytest.mark.unit
def test_complete_run(db_session, test_user):
    """Test completing a run."""
    # Create test script and case
    script_data = TestScriptCreate(name="Test Script")
    script = test_service.create_test_script(db_session, script_data, test_user.id)
    
    case_data = TestCaseCreate(test_script_id=script.id, name="Test Case")
    case = case_service.create_test_case(db_session, case_data, test_user.id)
    
    # Create, start, and complete run
    run = execution_service.create_run(db_session, case.id, test_user.id)
    execution_service.start_run(db_session, run.run_id)
    execution_service.complete_run(
        db_session, 
        run.run_id, 
        ExecutionStatus.PASSED,
        log_content="Test passed successfully"
    )
    
    # Verify status and completion
    db_session.refresh(run)
    assert run.status == ExecutionStatus.PASSED
    assert run.finished_at is not None
