from typing import List, Dict, Any
from datetime import datetime

from ..database.models import QueueItem, QueueStatus, TestCase
from ..database.connection import get_db_context
from .execution_service import execution_service
import logging

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing test execution queue."""
    
    # PUBLIC_INTERFACE
    def add_to_queue(self, case_ids: List[str], priority: int = 1, config: Dict[str, Any] = None) -> List[str]:
        """
        Add test cases to the execution queue.
        
        Args:
            case_ids: List of test case IDs to queue
            priority: Priority level (higher number = higher priority)
            config: Optional execution configuration
            
        Returns:
            List of queue item IDs
        """
        queue_item_ids = []
        
        with get_db_context() as db:
            for case_id in case_ids:
                # Verify test case exists
                test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
                if not test_case:
                    logger.warning(f"Test case {case_id} not found, skipping")
                    continue
                
                # Check if already queued
                existing = db.query(QueueItem).filter(
                    QueueItem.case_id == case_id,
                    QueueItem.status == QueueStatus.QUEUED
                ).first()
                
                if existing:
                    logger.warning(f"Test case {case_id} already queued")
                    continue
                
                queue_item = QueueItem(
                    case_id=case_id,
                    status=QueueStatus.QUEUED,
                    priority=priority,
                    config=config,
                    queued_at=datetime.utcnow()
                )
                
                db.add(queue_item)
                db.flush()  # Get the ID
                queue_item_ids.append(queue_item.id)
            
            db.commit()
        
        logger.info(f"Added {len(queue_item_ids)} items to queue")
        return queue_item_ids
    
    # PUBLIC_INTERFACE
    def remove_from_queue(self, case_id: str) -> bool:
        """
        Remove a test case from the queue.
        
        Args:
            case_id: ID of the test case to remove
            
        Returns:
            True if removed, False if not found or already processing
        """
        with get_db_context() as db:
            queue_item = db.query(QueueItem).filter(
                QueueItem.case_id == case_id,
                QueueItem.status == QueueStatus.QUEUED
            ).first()
            
            if not queue_item:
                return False
            
            db.delete(queue_item)
            db.commit()
            
        logger.info(f"Removed test case {case_id} from queue")
        return True
    
    # PUBLIC_INTERFACE
    def get_queue_status(self) -> List[Dict[str, Any]]:
        """
        Get current queue status.
        
        Returns:
            List of queue items with their status
        """
        with get_db_context() as db:
            queue_items = db.query(QueueItem).order_by(
                QueueItem.priority.desc(),
                QueueItem.queued_at.asc()
            ).all()
            
            result = []
            for item in queue_items:
                test_case = db.query(TestCase).filter(TestCase.id == item.case_id).first()
                result.append({
                    "id": item.id,
                    "case_id": item.case_id,
                    "case_name": test_case.name if test_case else "Unknown",
                    "status": item.status.value,
                    "priority": item.priority,
                    "queued_at": item.queued_at.isoformat(),
                    "started_at": item.started_at.isoformat() if item.started_at else None,
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                })
            
            return result
    
    # PUBLIC_INTERFACE
    async def process_queue(self, user_id: str, max_concurrent: int = 1):
        """
        Process queued items for execution.
        
        Args:
            user_id: ID of user processing the queue
            max_concurrent: Maximum number of concurrent executions
        """
        with get_db_context() as db:
            # Get next items to process
            queued_items = db.query(QueueItem).filter(
                QueueItem.status == QueueStatus.QUEUED
            ).order_by(
                QueueItem.priority.desc(),
                QueueItem.queued_at.asc()
            ).limit(max_concurrent).all()
            
            for item in queued_items:
                try:
                    # Mark as processing
                    item.status = QueueStatus.PROCESSING
                    item.started_at = datetime.utcnow()
                    db.commit()
                    
                    # Execute test case
                    run_id = await execution_service.execute_test_case(
                        item.case_id,
                        user_id,
                        item.config
                    )
                    
                    # Mark as completed
                    item.status = QueueStatus.COMPLETED
                    item.completed_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Successfully processed queue item {item.id}, run_id: {run_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing queue item {item.id}: {e}")
                    item.status = QueueStatus.FAILED
                    item.completed_at = datetime.utcnow()
                    db.commit()
    
    # PUBLIC_INTERFACE
    def clear_completed_items(self, older_than_hours: int = 24):
        """
        Clear completed queue items older than specified hours.
        
        Args:
            older_than_hours: Remove items completed more than this many hours ago
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        with get_db_context() as db:
            deleted_count = db.query(QueueItem).filter(
                QueueItem.status.in_([QueueStatus.COMPLETED, QueueStatus.FAILED]),
                QueueItem.completed_at < cutoff_time
            ).delete()
            
            db.commit()
            
        logger.info(f"Cleared {deleted_count} completed queue items")
        return deleted_count

# Global instance
queue_service = QueueService()
