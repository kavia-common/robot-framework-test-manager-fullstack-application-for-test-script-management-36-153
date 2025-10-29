"""
Test cases API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.session import get_db
from src.database.models import User
from src.schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from src.services.case_service import case_service
from src.services.auth_service import auth_service
from src.api.dependencies import get_current_user, get_client_info

router = APIRouter(prefix="/cases", tags=["Test Cases"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new test case")
async def create_test_case(
    case_data: TestCaseCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new test case.
    
    Args:
        case_data: Test case data
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Created test case information
    """
    try:
        case = case_service.create_test_case(db, case_data, current_user.id)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "create_test_case",
            resource_type="test_case",
            resource_id=case.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {"success": True, "data": {"id": case.id, "name": case.name}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", summary="List all test cases (with filtering)")
async def list_test_cases(
    test_script_id: Optional[str] = Query(None, description="Filter by test script ID"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List test cases with optional filtering and pagination.
    
    Args:
        test_script_id: Optional filter by test script ID
        name: Optional filter by name
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Pagination: Paginated list of test cases
    """
    skip = (page - 1) * page_size
    cases = case_service.list_test_cases(
        db, test_script_id=test_script_id, name=name, skip=skip, limit=page_size
    )
    total = case_service.get_total_count(db, test_script_id=test_script_id)
    
    return {
        "items": [TestCaseResponse.model_validate(c) for c in cases],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{case_id}", response_model=TestCaseResponse,
           summary="Retrieve details of a specific test case")
async def get_test_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get test case details by ID.
    
    Args:
        case_id: Test case ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TestCaseResponse: Test case details
        
    Raises:
        HTTPException: If test case not found
    """
    case = case_service.get_test_case(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    
    return TestCaseResponse.model_validate(case)


@router.put("/{case_id}", summary="Update a test case")
async def update_test_case(
    case_id: str,
    case_data: TestCaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a test case.
    
    Args:
        case_id: Test case ID
        case_data: Updated data
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Update confirmation
        
    Raises:
        HTTPException: If test case not found or update fails
    """
    try:
        case = case_service.update_test_case(db, case_id, case_data)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "update_test_case",
            resource_type="test_case",
            resource_id=case.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {"success": True, "data": {"id": case.id}, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete a test case")
async def delete_test_case(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a test case (soft delete).
    
    Args:
        case_id: Test case ID
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If test case not found
    """
    try:
        case_service.delete_test_case(db, case_id)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "delete_test_case",
            resource_type="test_case",
            resource_id=case_id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
