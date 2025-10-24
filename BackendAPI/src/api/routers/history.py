"""
History router.
Handles run history retrieval and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.schemas.test_schemas import RunHistoryResponse, PaginationResponse
from src.services.execution_service import execution_service
from src.core.security import get_current_user

router = APIRouter(prefix="/history", tags=["Run History"])


@router.get(
    "",
    response_model=PaginationResponse,
    summary="List run history (with filtering and pagination)"
)
async def get_history(
    case_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List run history with optional filtering and pagination.
    
    - **case_id**: Optional filter by test case UUID
    - **status**: Optional filter by execution status (pending, running, passed, failed, error)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    
    Returns paginated list of run history entries with log URLs where available.
    """
    return execution_service.get_run_history(db, case_id, status, page, page_size)


@router.get(
    "/{run_id}",
    response_model=RunHistoryResponse,
    summary="Retrieve details and logs for a specific run"
)
async def get_run_details(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information for a specific test run.
    
    - **run_id**: UUID of the run history entry
    
    Returns run details including case ID, status, timestamps, and log URL.
    """
    run_details = execution_service.get_run_details(db, run_id)
    if not run_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run history not found"
        )
    return run_details
