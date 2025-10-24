from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ...database.connection import get_db
from ...database.models import TestCase, TestScript, User
from ...auth.rbac import require_permission, Permission

router = APIRouter(prefix="/cases", tags=["test-cases"])

class TestCaseCreate(BaseModel):
    test_script_id: str
    name: str
    description: str = ""
    variables: Dict[str, Any] = {}

class TestCaseUpdate(BaseModel):
    name: str = None
    description: str = None
    variables: Dict[str, Any] = None

class TestCaseResponse(BaseModel):
    id: str
    test_script_id: str
    name: str
    description: str
    variables: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StandardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = None

class PaginationResponse(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int

# PUBLIC_INTERFACE
@router.post("/", response_model=StandardResponse, status_code=201)
async def create_test_case(
    test_case_data: TestCaseCreate,
    current_user: User = Depends(require_permission(Permission.CREATE_TEST_CASE)),
    db: Session = Depends(get_db)
):
    """
    Create a new test case.
    
    Args:
        test_case_data: Test case data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Standard response with created test case data
    """
    # Verify test script exists
    test_script = db.query(TestScript).filter(TestScript.id == test_case_data.test_script_id).first()
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test script not found"
        )
    
    try:
        test_case = TestCase(
            test_script_id=test_case_data.test_script_id,
            name=test_case_data.name,
            description=test_case_data.description,
            variables=test_case_data.variables,
            created_by=current_user.id
        )
        
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        
        return StandardResponse(
            success=True,
            data={"test_case_id": test_case.id, "message": "Test case created successfully"}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create test case: {str(e)}"
        )

# PUBLIC_INTERFACE
@router.get("/", response_model=PaginationResponse)
async def list_test_cases(
    test_script_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_permission(Permission.READ_TEST_CASE)),
    db: Session = Depends(get_db)
):
    """
    List all test cases with optional filtering and pagination.
    
    Args:
        test_script_id: Optional filter by test script ID
        name: Optional filter by test case name (partial match)
        page: Page number (starts from 1)
        page_size: Number of items per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated list of test cases
    """
    offset = (page - 1) * page_size
    
    query = db.query(TestCase)
    
    # Apply filters
    if test_script_id:
        query = query.filter(TestCase.test_script_id == test_script_id)
    
    if name:
        query = query.filter(TestCase.name.ilike(f"%{name}%"))
    
    total = query.count()
    test_cases = query.offset(offset).limit(page_size).all()
    
    return PaginationResponse(
        items=[TestCaseResponse.from_orm(case) for case in test_cases],
        total=total,
        page=page,
        page_size=page_size
    )

# PUBLIC_INTERFACE
@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    case_id: str,
    current_user: User = Depends(require_permission(Permission.READ_TEST_CASE)),
    db: Session = Depends(get_db)
):
    """
    Retrieve details of a specific test case.
    
    Args:
        case_id: ID of the test case
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Test case details
    """
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    return TestCaseResponse.from_orm(test_case)

# PUBLIC_INTERFACE
@router.put("/{case_id}", response_model=StandardResponse)
async def update_test_case(
    case_id: str,
    test_case_data: TestCaseUpdate,
    current_user: User = Depends(require_permission(Permission.UPDATE_TEST_CASE)),
    db: Session = Depends(get_db)
):
    """
    Update a test case.
    
    Args:
        case_id: ID of the test case to update
        test_case_data: Updated test case data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Standard response indicating success or failure
    """
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    try:
        # Update only provided fields
        update_data = test_case_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_case, field, value)
        
        db.commit()
        
        return StandardResponse(
            success=True,
            data={"message": "Test case updated successfully"}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update test case: {str(e)}"
        )

# PUBLIC_INTERFACE
@router.delete("/{case_id}", status_code=204)
async def delete_test_case(
    case_id: str,
    current_user: User = Depends(require_permission(Permission.DELETE_TEST_CASE)),
    db: Session = Depends(get_db)
):
    """
    Delete a test case.
    
    Args:
        case_id: ID of the test case to delete
        current_user: Current authenticated user
        db: Database session
    """
    test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found"
        )
    
    try:
        db.delete(test_case)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete test case: {str(e)}"
        )
