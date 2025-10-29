"""
Run history API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database.session import get_db
from src.database.models import User
from src.schemas.run_history import RunHistoryResponse, LogResponse
from src.services.history_service import history_service
from src.api.dependencies import get_current_user

router = APIRouter(tags=["History"])


@router.get("/history", summary="List run history (with filtering and pagination)")
async def list_run_history(
    case_id: Optional[str] = Query(None, description="Filter by case ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List run history with optional filtering and pagination.
    
    Args:
        case_id: Optional filter by case ID
        status: Optional filter by execution status
        page: Page number
        page_size: Items per page
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Pagination: Paginated list of run histories
    """
    skip = (page - 1) * page_size
    histories = history_service.list_run_histories(
        db, case_id=case_id, status=status, skip=skip, limit=page_size
    )
    total = history_service.get_total_count(db, case_id=case_id, status=status)
    
    return {
        "items": [RunHistoryResponse.model_validate(h) for h in histories],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/history/{run_id}", response_model=RunHistoryResponse,
           summary="Retrieve details and logs for a specific run")
async def get_run_history(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get run history details by run ID.
    
    Args:
        run_id: Run ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        RunHistoryResponse: Run history details
        
    Raises:
        HTTPException: If run not found
    """
    run = history_service.get_run_history(db, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    
    return RunHistoryResponse.model_validate(run)


@router.get("/logs/{run_id}", response_model=LogResponse,
           summary="Download or preview execution logs")
async def get_logs(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get presigned URL for downloading execution logs.
    
    Args:
        run_id: Run ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        LogResponse: Presigned URL for log download
        
    Raises:
        HTTPException: If run or logs not found
    """
    log_url = history_service.get_log_url(db, run_id)
    
    if not log_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logs not found for this run"
        )
    
    return LogResponse(log_url=log_url)
