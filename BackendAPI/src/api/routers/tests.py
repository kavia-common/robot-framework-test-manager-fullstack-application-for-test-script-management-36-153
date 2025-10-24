from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from src.database.connection import get_db
from src.database.models import TestScript
from src.services.minio_service import minio_service

router = APIRouter(prefix="/tests", tags=["test-scripts"])

class TestScriptCreate(BaseModel):
    name: str
    description: str = ""
    content: str = ""
    script_metadata: Dict[str, Any] = {}

class TestScriptUpdate(BaseModel):
    name: str = None
    description: str = None
    content: str = None
    script_metadata: Dict[str, Any] = None

class TestScriptResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    script_metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True

class StandardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = None

class PaginationResponse(BaseModel):
    items: List[TestScriptResponse]
    total: int
    page: int
    page_size: int

# Default system user ID for operations
SYSTEM_USER_ID = "system"

# PUBLIC_INTERFACE
@router.post("/", response_model=StandardResponse, status_code=201)
async def create_test_script(
    test_script_data: TestScriptCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new test script.
    
    Args:
        test_script_data: Test script data
        db: Database session
        
    Returns:
        Standard response with created test script data
    """
    try:
        test_script = TestScript(
            name=test_script_data.name,
            description=test_script_data.description,
            content=test_script_data.content,
            script_metadata=test_script_data.script_metadata,
            created_by=SYSTEM_USER_ID
        )
        
        db.add(test_script)
        db.commit()
        db.refresh(test_script)
        
        return StandardResponse(
            success=True,
            data={"test_script_id": test_script.id, "message": "Test script created successfully"}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create test script: {str(e)}"
        )

# PUBLIC_INTERFACE
@router.get("/", response_model=PaginationResponse)
async def list_test_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all test scripts with pagination.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        Paginated list of test scripts
    """
    offset = (page - 1) * page_size
    
    query = db.query(TestScript)
    total = query.count()
    
    test_scripts = query.offset(offset).limit(page_size).all()
    
    return PaginationResponse(
        items=[TestScriptResponse.from_orm(script) for script in test_scripts],
        total=total,
        page=page,
        page_size=page_size
    )

# PUBLIC_INTERFACE
@router.get("/{test_id}", response_model=TestScriptResponse)
async def get_test_script(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve details of a specific test script.
    
    Args:
        test_id: ID of the test script
        db: Database session
        
    Returns:
        Test script details
    """
    test_script = db.query(TestScript).filter(TestScript.id == test_id).first()
    
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    
    return TestScriptResponse.from_orm(test_script)

# PUBLIC_INTERFACE
@router.put("/{test_id}", response_model=StandardResponse)
async def update_test_script(
    test_id: str,
    test_script_data: TestScriptUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a test script.
    
    Args:
        test_id: ID of the test script to update
        test_script_data: Updated test script data
        db: Database session
        
    Returns:
        Standard response indicating success or failure
    """
    test_script = db.query(TestScript).filter(TestScript.id == test_id).first()
    
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    
    try:
        # Update only provided fields
        update_data = test_script_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_script, field, value)
        
        db.commit()
        
        return StandardResponse(
            success=True,
            data={"message": "Test script updated successfully"}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update test script: {str(e)}"
        )

# PUBLIC_INTERFACE
@router.delete("/{test_id}", status_code=204)
async def delete_test_script(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a test script.
    
    Args:
        test_id: ID of the test script to delete
        db: Database session
    """
    test_script = db.query(TestScript).filter(TestScript.id == test_id).first()
    
    if not test_script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test script not found"
        )
    
    try:
        # Delete associated file from MinIO if exists
        if test_script.file_path:
            minio_service.delete_file(test_script.file_path)
        
        db.delete(test_script)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete test script: {str(e)}"
        )
