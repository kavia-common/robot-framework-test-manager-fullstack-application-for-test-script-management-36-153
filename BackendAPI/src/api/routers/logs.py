"""
Logs router.
Handles execution log retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.test_schemas import LogResponse
from src.services.execution_service import execution_service
from src.core.security import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get(
    "/{run_id}",
    response_model=LogResponse,
    summary="Download or preview execution logs"
)
async def get_logs(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get execution logs for a specific run.
    
    - **run_id**: UUID of the run history entry
    
    Returns a presigned URL to download/view the log file from MinIO.
    The URL is valid for 1 hour.
    """
    log_url = execution_service.get_logs(db, run_id)
    if not log_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logs not found for this run"
        )
    return LogResponse(log_url=log_url)
