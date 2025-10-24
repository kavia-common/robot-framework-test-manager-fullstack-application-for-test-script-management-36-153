from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...database.connection import get_db
from ...database.models import TestCase, User
from ...auth.rbac import require_permission, Permission
from ...services.execution_service import execution_service

router = APIRouter(prefix="/execute", tags=["execution"])

class ExecutionRequest(BaseModel):
    case_ids: List[str]
    run_type: str  # "ad_hoc" or "queued"
    config: Dict[str, Any] = {}

class StandardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = None

# PUBLIC_INTERFACE
@router.post("/", response_model=StandardResponse, status_code=202)
async def execute_test_cases(
    execution_request: ExecutionRequest,
    current_user: User = Depends(require_permission(Permission.EXECUTE_TEST)),
    db: Session = Depends(get_db)
):
    """
    Execute one or more test cases (ad hoc or queued).
    
    Args:
        execution_request: Execution request containing case IDs and configuration
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Standard response with execution details
    """
    if not execution_request.case_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No test cases specified for execution"
        )
    
    # Validate that all test cases exist
    for case_id in execution_request.case_ids:
        test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test case {case_id} not found"
            )
    
    try:
        if execution_request.run_type == "ad_hoc":
            # Execute immediately
            run_ids = await execution_service.execute_multiple_test_cases(
                execution_request.case_ids,
                current_user.id,
                execution_request.config
            )
            
            return StandardResponse(
                success=True,
                data={
                    "message": f"Started execution of {len(run_ids)} test cases",
                    "run_ids": run_ids,
                    "run_type": "ad_hoc"
                }
            )
            
        elif execution_request.run_type == "queued":
            # Add to queue for later execution
            from ...services.queue_service import queue_service
            
            queue_item_ids = queue_service.add_to_queue(
                execution_request.case_ids,
                priority=1,  # Default priority
                config=execution_request.config
            )
            
            return StandardResponse(
                success=True,
                data={
                    "message": f"Added {len(queue_item_ids)} test cases to execution queue",
                    "queue_item_ids": queue_item_ids,
                    "run_type": "queued"
                }
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid run_type. Must be 'ad_hoc' or 'queued'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute test cases: {str(e)}"
        )
