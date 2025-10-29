"""
Queue management API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from src.database.session import get_db
from src.database.models import User
from src.schemas.queue import QueueItemResponse, QueueAddRequest
from src.services.queue_service import queue_service
from src.services.auth_service import auth_service
from src.api.dependencies import get_current_user, get_client_info

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("", response_model=List[QueueItemResponse],
           summary="List currently queued test cases")
async def get_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all currently queued test cases.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[QueueItemResponse]: List of queued items ordered by priority
    """
    items = queue_service.get_queue(db)
    return [QueueItemResponse.model_validate(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED,
            summary="Add test case(s) to queue")
async def add_to_queue(
    queue_data: QueueAddRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add one or more test cases to the execution queue.
    
    Args:
        queue_data: Queue request with case IDs
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Queue confirmation
    """
    try:
        items = queue_service.add_to_queue(db, queue_data.case_ids, current_user.id)
        
        # Log audit event
        client_info = get_client_info(request)
        auth_service.log_audit_event(
            db, current_user.id, "add_to_queue",
            resource_type="queue",
            details={"case_ids": queue_data.case_ids},
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {
            "success": True,
            "data": {
                "queued_count": len(items),
                "message": f"Added {len(items)} test case(s) to queue"
            },
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT,
              summary="Remove a test case from queue")
async def remove_from_queue(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a test case from the execution queue.
    
    Args:
        case_id: Test case ID to remove
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If case not found in queue
    """
    success = queue_service.remove_from_queue(db, case_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test case not found in queue"
        )
    
    # Log audit event
    client_info = get_client_info(request)
    auth_service.log_audit_event(
        db, current_user.id, "remove_from_queue",
        resource_type="queue",
        resource_id=case_id,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"]
    )
    
    return None
