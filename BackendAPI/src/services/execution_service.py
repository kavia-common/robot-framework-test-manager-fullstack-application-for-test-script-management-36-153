"""
Execution service for managing test execution, queuing, and run history.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from src.database.models import QueueItem, RunHistory, TestCase, StatusEnum, RunTypeEnum
from src.schemas.test_schemas import (
    QueueItemResponse, RunHistoryResponse, PaginationResponse
)
from src.services.storage_service import storage_service

logger = logging.getLogger(__name__)


class ExecutionService:
    """Service for test execution, queuing, and history management"""
    
    # PUBLIC_INTERFACE
    def add_to_queue(self, db: Session, case_ids: List[str], user_id: str) -> List[QueueItemResponse]:
        """
        Add test cases to the execution queue.
        
        Args:
            db: Database session
            case_ids: List of test case IDs
            user_id: ID of user adding to queue
            
        Returns:
            List of created queue items
        """
        queue_items = []
        for case_id in case_ids:
            # Check if test case exists
            case = db.query(TestCase).filter(TestCase.id == case_id).first()
            if not case:
                continue
            
            # Check if already in queue
            existing = db.query(QueueItem).filter(
                QueueItem.case_id == case_id,
                QueueItem.status == StatusEnum.PENDING
            ).first()
            if existing:
                continue
            
            queue_item = QueueItem(
                case_id=case_id,
                status=StatusEnum.PENDING,
                queued_by=user_id
            )
            db.add(queue_item)
            queue_items.append(queue_item)
        
        db.commit()
        return [QueueItemResponse.model_validate(qi) for qi in queue_items]
    
    # PUBLIC_INTERFACE
    def get_queue(self, db: Session) -> List[QueueItemResponse]:
        """
        Get all items in the execution queue.
        
        Args:
            db: Database session
            
        Returns:
            List of queue items
        """
        queue_items = db.query(QueueItem).order_by(QueueItem.priority.desc(), QueueItem.queued_at).all()
        return [QueueItemResponse.model_validate(qi) for qi in queue_items]
    
    # PUBLIC_INTERFACE
    def remove_from_queue(self, db: Session, case_id: str) -> bool:
        """
        Remove a test case from the execution queue.
        
        Args:
            db: Database session
            case_id: Test case ID
            
        Returns:
            True if removed, False if not found
        """
        queue_item = db.query(QueueItem).filter(
            QueueItem.case_id == case_id,
            QueueItem.status == StatusEnum.PENDING
        ).first()
        
        if not queue_item:
            return False
        
        db.delete(queue_item)
        db.commit()
        return True
    
    # PUBLIC_INTERFACE
    async def execute_tests(
        self, 
        db: Session, 
        case_ids: List[str], 
        run_type: str,
        user_id: str
    ) -> List[str]:
        """
        Execute test cases (creates run history entries and optionally adds to queue).
        
        Args:
            db: Database session
            case_ids: List of test case IDs to execute
            run_type: Type of run ('ad_hoc' or 'queued')
            user_id: ID of user triggering execution
            
        Returns:
            List of run history IDs
        """
        run_ids = []
        
        for case_id in case_ids:
            # Verify test case exists
            case = db.query(TestCase).filter(TestCase.id == case_id).first()
            if not case:
                continue
            
            # Create run history entry
            run_type_enum = RunTypeEnum.AD_HOC if run_type == "ad_hoc" else RunTypeEnum.QUEUED
            run_history = RunHistory(
                case_id=case_id,
                run_type=run_type_enum,
                status=StatusEnum.PENDING,
                triggered_by=user_id
            )
            db.add(run_history)
            db.flush()
            
            # If queued, add to queue
            if run_type == "queued":
                self.add_to_queue(db, [case_id], user_id)
            
            run_ids.append(run_history.id)
        
        db.commit()
        
        # In a real implementation, this would trigger background tasks
        # For now, we just create the run history entries
        logger.info(f"Created {len(run_ids)} run history entries")
        
        return run_ids
    
    # PUBLIC_INTERFACE
    def get_run_history(
        self,
        db: Session,
        case_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginationResponse:
        """
        Get run history with optional filtering and pagination.
        
        Args:
            db: Database session
            case_id: Optional filter by test case ID
            status: Optional filter by status
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Paginated list of run history entries
        """
        query = db.query(RunHistory)
        
        if case_id:
            query = query.filter(RunHistory.case_id == case_id)
        if status:
            query = query.filter(RunHistory.status == status)
        
        total = query.count()
        offset = (page - 1) * page_size
        histories = query.order_by(RunHistory.created_at.desc()).offset(offset).limit(page_size).all()
        
        items = []
        for history in histories:
            log_url = None
            if history.logs:
                latest_log = history.logs[0]
                if latest_log.log_file_path:
                    try:
                        log_url = storage_service.get_log_url(latest_log.log_file_path)
                    except Exception as e:
                        logger.error(f"Error generating log URL: {e}")
            
            items.append(RunHistoryResponse(
                run_id=history.id,
                case_id=history.case_id,
                status=history.status.value,
                started_at=history.started_at,
                finished_at=history.finished_at,
                log_url=log_url
            ))
        
        return PaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # PUBLIC_INTERFACE
    def get_run_details(self, db: Session, run_id: str) -> Optional[RunHistoryResponse]:
        """
        Get details of a specific run.
        
        Args:
            db: Database session
            run_id: Run history ID
            
        Returns:
            Run history details if found, None otherwise
        """
        history = db.query(RunHistory).filter(RunHistory.id == run_id).first()
        if not history:
            return None
        
        log_url = None
        if history.logs:
            latest_log = history.logs[0]
            if latest_log.log_file_path:
                try:
                    log_url = storage_service.get_log_url(latest_log.log_file_path)
                except Exception as e:
                    logger.error(f"Error generating log URL: {e}")
        
        return RunHistoryResponse(
            run_id=history.id,
            case_id=history.case_id,
            status=history.status.value,
            started_at=history.started_at,
            finished_at=history.finished_at,
            log_url=log_url
        )
    
    # PUBLIC_INTERFACE
    def get_logs(self, db: Session, run_id: str) -> Optional[str]:
        """
        Get logs for a specific run.
        
        Args:
            db: Database session
            run_id: Run history ID
            
        Returns:
            Log URL if found, None otherwise
        """
        history = db.query(RunHistory).filter(RunHistory.id == run_id).first()
        if not history or not history.logs:
            return None
        
        latest_log = history.logs[0]
        if latest_log.log_file_path:
            try:
                return storage_service.get_log_url(latest_log.log_file_path)
            except Exception as e:
                logger.error(f"Error generating log URL: {e}")
                return None
        
        return None


# Global execution service instance
execution_service = ExecutionService()
