"""
Test scripts router.
Handles CRUD operations for test scripts.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.test_schemas import (
    TestScriptCreate, TestScriptUpdate, TestScriptResponse,
    StandardResponse, PaginationResponse
)
from src.services.test_service import test_service
from src.core.security import get_current_user

router = APIRouter(prefix="/tests", tags=["Test Scripts"])


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test script"
)
async def create_test(
    test_data: TestScriptCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new test script.
    
    - **name**: Name of the test script (required)
    - **description**: Optional description
    - **metadata**: Optional metadata as JSON object
    
    Returns the created test script with ID and timestamps.
    """
    user_id = current_user.get("sub")
    test_script = test_service.create_test_script(db, test_data, user_id)
    return StandardResponse(success=True, data=test_script.model_dump())


@router.get(
    "",
    response_model=PaginationResponse,
    summary="List all test scripts"
)
async def list_tests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all test scripts with pagination.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns paginated list of test scripts.
    """
    return test_service.list_test_scripts(db, page, page_size)


@router.get(
    "/{test_id}",
    response_model=TestScriptResponse,
    summary="Retrieve details of a specific test script"
)
async def get_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific test script by ID.
    
    - **test_id**: UUID of the test script
    
    Returns test script details including metadata and timestamps.
    """
    test_script = test_service.get_test_script(db, test_id)
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    return test_script


@router.put(
    "/{test_id}",
    response_model=StandardResponse,
    summary="Update a test script"
)
async def update_test(
    test_id: str,
    test_data: TestScriptUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing test script.
    
    - **test_id**: UUID of the test script
    - **name**: Optional new name
    - **description**: Optional new description
    - **metadata**: Optional new metadata
    
    Returns the updated test script.
    """
    test_script = test_service.update_test_script(db, test_id, test_data)
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    return StandardResponse(success=True, data=test_script.model_dump())


@router.delete(
    "/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test script"
)
async def delete_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a test script.
    
    - **test_id**: UUID of the test script
    
    Deletes the test script and all associated test cases.
    Returns 204 No Content on success.
    """
    success = test_service.delete_test_script(db, test_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    return None
