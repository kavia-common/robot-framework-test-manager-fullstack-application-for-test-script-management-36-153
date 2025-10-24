"""
Queue router.
Handles test execution queue management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.schemas.test_schemas import QueueItemResponse, QueueAddRequest, StandardResponse
from src.services.execution_service import execution_service
from src.core.security import get_current_user

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get(
    "",
    response_model=List[QueueItemResponse],
    summary="List currently queued test cases"
)
async def get_queue(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve the current execution queue.
    
    Returns a list of queued test cases ordered by priority and queue time.
    Each item includes case ID, status, priority, and queued timestamp.
    """
    return execution_service.get_queue(db)


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add test case(s) to queue"
)
async def add_to_queue(
    queue_data: QueueAddRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add one or more test cases to the execution queue.
    
    - **case_ids**: List of test case UUIDs to add to queue
    
    Returns list of created queue items.
    Skips test cases that are already in the queue.
    """
    user_id = current_user.get("sub")
    queue_items = execution_service.add_to_queue(db, queue_data.case_ids, user_id)
    
    return StandardResponse(
        success=True,
        data={
            "queue_items": [qi.model_dump() for qi in queue_items],
            "message": f"Added {len(queue_items)} test cases to queue"
        }
    )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a test case from queue"
)
async def remove_from_queue(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a test case from the execution queue.
    
    - **case_id**: UUID of the test case to remove
    
    Returns 204 No Content on success.
    Only removes pending queue items.
    """
    success = execution_service.remove_from_queue(db, case_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue item not found or already executing"
        )
    return None
