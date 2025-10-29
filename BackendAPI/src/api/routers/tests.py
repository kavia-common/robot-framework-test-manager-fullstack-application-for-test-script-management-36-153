"""
Test scripts API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User
from src.schemas.test_script import TestScriptCreate, TestScriptUpdate, TestScriptResponse
from src.services.test_service import test_service
from src.services.auth_service import auth_service
from src.api.dependencies import get_current_user, get_client_info

router = APIRouter(prefix="/tests", tags=["Test Scripts"])


# Response schemas
class StandardResponse(dict):
    """Standard API response."""
    pass


class Pagination(dict):
    """Pagination response."""
    pass


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED,
            summary="Create a new test script")
async def create_test_script(
    script_data: TestScriptCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new test script.
    
    Args:
        script_data: Test script data
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Created test script information
    """
    try:
        script = test_service.create_test_script(db, script_data, current_user.id)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "create_test_script",
            resource_type="test_script",
            resource_id=script.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {"success": True, "data": {"id": script.id, "name": script.name}, "error": None}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=Pagination, summary="List all test scripts")
async def list_test_scripts(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all test scripts with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Pagination: Paginated list of test scripts
    """
    skip = (page - 1) * page_size
    scripts = test_service.list_test_scripts(db, skip=skip, limit=page_size)
    total = test_service.get_total_count(db)
    
    return {
        "items": [TestScriptResponse.model_validate(s) for s in scripts],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{test_id}", response_model=TestScriptResponse,
           summary="Retrieve details of a specific test script")
async def get_test_script(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get test script details by ID.
    
    Args:
        test_id: Test script ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        TestScriptResponse: Test script details
        
    Raises:
        HTTPException: If test script not found
    """
    script = test_service.get_test_script(db, test_id)
    if not script:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test script not found")
    
    return TestScriptResponse.model_validate(script)


@router.put("/{test_id}", response_model=StandardResponse, summary="Update a test script")
async def update_test_script(
    test_id: str,
    script_data: TestScriptUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a test script.
    
    Args:
        test_id: Test script ID
        script_data: Updated data
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Update confirmation
        
    Raises:
        HTTPException: If test script not found or update fails
    """
    try:
        script = test_service.update_test_script(db, test_id, script_data)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "update_test_script",
            resource_type="test_script",
            resource_id=script.id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {"success": True, "data": {"id": script.id}, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT,
              summary="Delete a test script")
async def delete_test_script(
    test_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a test script (soft delete).
    
    Args:
        test_id: Test script ID
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If test script not found
    """
    try:
        test_service.delete_test_script(db, test_id)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "delete_test_script",
            resource_type="test_script",
            resource_id=test_id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
