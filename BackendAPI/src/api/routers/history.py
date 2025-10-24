from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json

from src.database.connection import get_db
from src.database.models import RunHistory
from src.services.minio_service import minio_service

router = APIRouter(prefix="/history", tags=["history"])

class RunHistoryResponse(BaseModel):
    run_id: str
    case_id: str
    status: str
    started_at: datetime
    finished_at: datetime = None
    log_url: str = None
    
    class Config:
        from_attributes = True

class PaginationResponse(BaseModel):
    items: List[RunHistoryResponse]
    total: int
    page: int
    page_size: int

class LogResponse(BaseModel):
    log_url: str

# PUBLIC_INTERFACE
@router.get("/", response_model=PaginationResponse)
async def list_run_history(
    case_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List run history with optional filtering and pagination.
    
    Args:
        case_id: Optional filter by test case ID
        status: Optional filter by execution status
        page: Page number (starts from 1)
        page_size: Number of items per page
        db: Database session
        
    Returns:
        Paginated list of run history
    """
    offset = (page - 1) * page_size
    
    query = db.query(RunHistory)
    
    # Apply filters
    if case_id:
        query = query.filter(RunHistory.case_id == case_id)
    
    if status:
        query = query.filter(RunHistory.status == status)
    
    # Order by most recent first
    query = query.order_by(RunHistory.started_at.desc())
    
    total = query.count()
    run_histories = query.offset(offset).limit(page_size).all()
    
    # Process run histories to include log URLs
    items = []
    for run_history in run_histories:
        item_data = {
            "run_id": run_history.id,
            "case_id": run_history.case_id,
            "status": run_history.status.value,
            "started_at": run_history.started_at,
            "finished_at": run_history.finished_at,
            "log_url": None
        }
        
        # Generate log URL if log files exist
        if run_history.log_file_path:
            try:
                log_files = json.loads(run_history.log_file_path)
                if "log.html" in log_files:
                    item_data["log_url"] = minio_service.get_file_url(log_files["log.html"])
            except (json.JSONDecodeError, Exception):
                pass
        
        items.append(RunHistoryResponse(**item_data))
    
    return PaginationResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

# PUBLIC_INTERFACE
@router.get("/{run_id}", response_model=RunHistoryResponse)
async def get_run_history(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve details and logs for a specific run.
    
    Args:
        run_id: ID of the run to retrieve
        db: Database session
        
    Returns:
        Run history details
    """
    run_history = db.query(RunHistory).filter(RunHistory.id == run_id).first()
    
    if not run_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run history not found"
        )
    
    # Generate log URL if available
    log_url = None
    if run_history.log_file_path:
        try:
            log_files = json.loads(run_history.log_file_path)
            if "log.html" in log_files:
                log_url = minio_service.get_file_url(log_files["log.html"])
        except (json.JSONDecodeError, Exception):
            pass
    
    return RunHistoryResponse(
        run_id=run_history.id,
        case_id=run_history.case_id,
        status=run_history.status.value,
        started_at=run_history.started_at,
        finished_at=run_history.finished_at,
        log_url=log_url
    )

# PUBLIC_INTERFACE
@router.get("/logs/{run_id}", response_model=LogResponse)
async def get_execution_logs(
    run_id: str,
    db: Session = Depends(get_db)
):
    """
    Download or preview execution logs for a specific run.
    
    Args:
        run_id: ID of the run to get logs for
        db: Database session
        
    Returns:
        Log download URL
    """
    run_history = db.query(RunHistory).filter(RunHistory.id == run_id).first()
    
    if not run_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run history not found"
        )
    
    if not run_history.log_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No logs available for this run"
        )
    
    try:
        log_files = json.loads(run_history.log_file_path)
        
        # Prefer HTML log, fallback to XML output
        log_file = log_files.get("log.html") or log_files.get("output.xml")
        
        if not log_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log files not found"
            )
        
        # Generate presigned URL for log access
        log_url = minio_service.get_file_url(log_file, expires_in_seconds=3600)
        
        return LogResponse(log_url=log_url)
        
    except (json.JSONDecodeError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accessing log files: {str(e)}"
        )
