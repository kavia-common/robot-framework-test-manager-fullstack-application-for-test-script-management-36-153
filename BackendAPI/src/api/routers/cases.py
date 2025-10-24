"""
Test cases router.
Handles CRUD operations for test cases.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.schemas.test_schemas import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    StandardResponse, PaginationResponse
)
from src.services.test_service import test_service
from src.core.security import get_current_user

router = APIRouter(prefix="/cases", tags=["Test Cases"])


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test case"
)
async def create_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new test case.
    
    - **test_script_id**: UUID of parent test script (required)
    - **name**: Name of the test case (required)
    - **description**: Optional description
    - **variables**: Optional variables as JSON object
    
    Returns the created test case with ID and timestamps.
    """
    test_case = test_service.create_test_case(db, case_data)
    return StandardResponse(success=True, data=test_case.model_dump())


@router.get(
    "",
    response_model=PaginationResponse,
    summary="List all test cases (with filtering)"
)
async def list_cases(
    test_script_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all test cases with optional filtering and pagination.
    
    - **test_script_id**: Optional filter by test script UUID
    - **name**: Optional filter by case name (partial match)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns paginated list of test cases.
    """
    return test_service.list_test_cases(db, test_script_id, name, page, page_size)


@router.get(
    "/{case_id}",
    response_model=TestCaseResponse,
    summary="Retrieve details of a specific test case"
)
async def get_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific test case by ID.
    
    - **case_id**: UUID of the test case
    
    Returns test case details including variables and timestamps.
    """
    test_case = test_service.get_test_case(db, case_id)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    return test_case


@router.put(
    "/{case_id}",
    response_model=StandardResponse,
    summary="Update a test case"
)
async def update_case(
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing test case.
    
    - **case_id**: UUID of the test case
    - **test_script_id**: Optional new parent test script UUID
    - **name**: Optional new name
    - **description**: Optional new description
    - **variables**: Optional new variables
    
    Returns the updated test case.
    """
    test_case = test_service.update_test_case(db, case_id, case_data)
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    return StandardResponse(success=True, data=test_case.model_dump())


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test case"
)
async def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a test case.
    
    - **case_id**: UUID of the test case
    
    Deletes the test case and all associated queue items and run history.
    Returns 204 No Content on success.
    """
    success = test_service.delete_test_case(db, case_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    return None
