"""
Test execution API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.database.models import User
from src.schemas.queue import ExecuteRequest
from src.services.execution_service import execution_service
from src.services.queue_service import queue_service
from src.services.auth_service import auth_service
from src.api.dependencies import get_current_user, get_client_info

router = APIRouter(prefix="/execute", tags=["Execution"])


@router.post("", status_code=status.HTTP_202_ACCEPTED,
            summary="Execute one or more test cases (ad hoc or queued)")
async def execute_test_cases(
    execute_data: ExecuteRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute test cases either ad hoc or by adding to queue.
    
    Args:
        execute_data: Execution request with case IDs and run type
        request: Request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StandardResponse: Execution acknowledgment with run IDs or queue status
        
    Raises:
        HTTPException: If execution request is invalid
    """
    try:
        if execute_data.run_type == "ad_hoc":
            # Execute immediately
            run_ids = []
            for case_id in execute_data.case_ids:
                run_id = await execution_service.execute_test_case(db, case_id, current_user.id)
                run_ids.append(run_id)
            
            # Log audit event
            client_info = get_client_info(request)
            auth_service.log_audit_event(
                db, current_user.id, "execute_ad_hoc",
                resource_type="test_execution",
                details={"case_ids": execute_data.case_ids, "run_ids": run_ids},
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"]
            )
            
            return {
                "success": True,
                "data": {
                    "run_type": "ad_hoc",
                    "run_ids": run_ids,
                    "message": f"Started execution for {len(run_ids)} test case(s)"
                },
                "error": None
            }
            
        elif execute_data.run_type == "queued":
            # Add to queue
            queue_items = queue_service.add_to_queue(db, execute_data.case_ids, current_user.id)
            
            # Log audit event
            client_info = get_client_info(request)
            auth_service.log_audit_event(
                db, current_user.id, "queue_execution",
                resource_type="queue",
                details={"case_ids": execute_data.case_ids},
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"]
            )
            
            return {
                "success": True,
                "data": {
                    "run_type": "queued",
                    "queued_count": len(queue_items),
                    "message": f"Added {len(queue_items)} test case(s) to queue"
                },
                "error": None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid run_type. Must be 'ad_hoc' or 'queued'"
            )
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
