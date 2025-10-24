"""
Execution router.
Handles test case execution requests.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.test_schemas import ExecuteRequest, StandardResponse
from src.services.execution_service import execution_service
from src.core.security import get_current_user

router = APIRouter(prefix="/execute", tags=["Execution"])


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute one or more test cases (ad hoc or queued)"
)
async def execute_tests(
    execute_data: ExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger execution of one or more test cases.
    
    - **case_ids**: List of test case UUIDs to execute
    - **run_type**: Type of execution ('ad_hoc' for immediate, 'queued' for queue)
    
    For ad_hoc runs, execution starts immediately (background).
    For queued runs, test cases are added to the execution queue.
    
    Returns 202 Accepted with run IDs.
    """
    user_id = current_user.get("sub")
    
    try:
        run_ids = await execution_service.execute_tests(
            db,
            execute_data.case_ids,
            execute_data.run_type,
            user_id
        )
        
        return StandardResponse(
            success=True,
            data={"run_ids": run_ids, "message": f"Execution initiated for {len(run_ids)} test cases"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to execute tests: {str(e)}"
        )
