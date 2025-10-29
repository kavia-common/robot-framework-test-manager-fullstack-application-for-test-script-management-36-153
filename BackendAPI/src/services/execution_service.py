"""
Service for managing test execution.
"""

from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from src.database.models import RunHistory, ExecutionStatus
from src.services.storage_service import storage_service
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ExecutionService:
    """Service for test execution management."""
    
    # PUBLIC_INTERFACE
    def create_run(self, db: Session, case_id: str, user_id: str) -> RunHistory:
        """
        Create a new test run record.
        
        Args:
            db: Database session
            case_id: Test case ID
            user_id: User ID who triggered the run
            
        Returns:
            RunHistory: Created run history record
        """
        run = RunHistory(
            case_id=case_id,
            status=ExecutionStatus.PENDING,
            triggered_by=user_id
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        logger.info(f"Created run {run.run_id} for case {case_id}")
        return run
    
    # PUBLIC_INTERFACE
    def start_run(self, db: Session, run_id: str):
        """
        Mark a run as started.
        
        Args:
            db: Database session
            run_id: Run ID
        """
        run = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
        
        if run:
            run.status = ExecutionStatus.RUNNING
            run.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Started run {run_id}")
    
    # PUBLIC_INTERFACE
    def complete_run(self, db: Session, run_id: str, status: ExecutionStatus, 
                     log_content: str = None, error_message: str = None):
        """
        Mark a run as completed.
        
        Args:
            db: Database session
            run_id: Run ID
            status: Final execution status
            log_content: Log content to upload
            error_message: Error message if failed
        """
        run = db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
        
        if not run:
            logger.error(f"Run {run_id} not found")
            return
        
        run.status = status
        run.finished_at = datetime.utcnow()
        
        if error_message:
            run.error_message = error_message
        
        # Upload logs if provided
        if log_content:
            try:
                object_key = storage_service.upload_log(run_id, log_content)
                run.log_object_key = object_key
                run.log_url = storage_service.get_log_url(object_key)
            except Exception as e:
                logger.error(f"Failed to upload log for run {run_id}: {str(e)}")
        
        db.commit()
        logger.info(f"Completed run {run_id} with status {status.value}")
    
    # PUBLIC_INTERFACE
    async def execute_test_case(self, db: Session, case_id: str, user_id: str) -> str:
        """
        Execute a test case asynchronously.
        
        Args:
            db: Database session
            case_id: Test case ID
            user_id: User ID who triggered execution
            
        Returns:
            str: Run ID
        """
        # Create run record
        run = self.create_run(db, case_id, user_id)
        
        # Start execution in background
        asyncio.create_task(self._execute_background(db, run.run_id, case_id))
        
        return run.run_id
    
    async def _execute_background(self, db: Session, run_id: str, case_id: str):
        """
        Background task for executing test case.
        
        Args:
            db: Database session
            run_id: Run ID
            case_id: Test case ID
        """
        try:
            self.start_run(db, run_id)
            
            # TODO: Implement actual Robot Framework test execution
            # This is a placeholder for the actual execution logic
            await asyncio.sleep(2)  # Simulate execution
            
            # Mock log content
            log_content = f"Test execution log for run {run_id}\nCase: {case_id}\nStatus: PASSED"
            
            self.complete_run(db, run_id, ExecutionStatus.PASSED, log_content=log_content)
            
        except Exception as e:
            logger.error(f"Execution failed for run {run_id}: {str(e)}")
            self.complete_run(
                db, run_id, ExecutionStatus.ERROR, 
                error_message=str(e),
                log_content=f"Execution failed: {str(e)}"
            )


# Global execution service instance
execution_service = ExecutionService()
