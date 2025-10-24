from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import get_db
from src.services.queue_service import queue_service

router = APIRouter(prefix="/queue", tags=["queue"])

class QueueRequest(BaseModel):
    case_ids: List[str]
    priority: int = 1
    config: Dict[str, Any] = {}

class QueueItemResponse(BaseModel):
    id: str
    case_id: str
    case_name: str
    status: str
    priority: int
    queued_at: str
    started_at: str = None
    completed_at: str = None

class StandardResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: str = None

# PUBLIC_INTERFACE
@router.get("/", response_model=List[QueueItemResponse])
async def list_queue_items(
    db: Session = Depends(get_db)
):
    """
    List currently queued test cases.
    
    Args:
        db: Database session
        
    Returns:
        List of queue items with their status
    """
    queue_items = queue_service.get_queue_status()
    return [QueueItemResponse(**item) for item in queue_items]

# PUBLIC_INTERFACE
@router.post("/", response_model=StandardResponse, status_code=201)
async def add_to_queue(
    queue_request: QueueRequest,
    db: Session = Depends(get_db)
):
    """
    Add test case(s) to execution queue.
    
    Args:
        queue_request: Queue request containing case IDs and configuration
        db: Database session
        
    Returns:
        Standard response with queue operation result
    """
    if not queue_request.case_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No test cases specified for queueing"
        )
    
    try:
        queue_item_ids = queue_service.add_to_queue(
            queue_request.case_ids,
            queue_request.priority,
            queue_request.config
        )
        
        return StandardResponse(
            success=True,
            data={
                "message": f"Added {len(queue_item_ids)} test cases to queue",
                "queue_item_ids": queue_item_ids
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add test cases to queue: {str(e)}"
        )

# PUBLIC_INTERFACE
@router.delete("/{case_id}", status_code=204)
async def remove_from_queue(
    case_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove a test case from the execution queue.
    
    Args:
        case_id: ID of the test case to remove from queue
        db: Database session
    """
    success = queue_service.remove_from_queue(case_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found in queue or already processing"
        )
