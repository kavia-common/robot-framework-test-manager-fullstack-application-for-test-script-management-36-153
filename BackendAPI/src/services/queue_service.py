"""
Service for managing test execution queue.
"""

from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.database.models import QueueItem, QueueStatus
from src.utils.logging import get_logger

logger = get_logger(__name__)


class QueueService:
    """Service for queue management."""
    
    # PUBLIC_INTERFACE
    def add_to_queue(self, db: Session, case_ids: List[str], user_id: str, priority: int = 0) -> List[QueueItem]:
        """
        Add test cases to execution queue.
        
        Args:
            db: Database session
            case_ids: List of test case IDs
            user_id: User ID who queued the items
            priority: Queue priority (higher = higher priority)
            
        Returns:
            List[QueueItem]: Created queue items
        """
        queue_items = []
        
        for case_id in case_ids:
            # Check if already queued
            existing = db.query(QueueItem).filter(
                QueueItem.case_id == case_id,
                QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.RUNNING])
            ).first()
            
            if existing:
                logger.warning(f"Case {case_id} already in queue")
                continue
            
            item = QueueItem(
                case_id=case_id,
                status=QueueStatus.QUEUED,
                priority=priority,
                queued_by=user_id
            )
            
            db.add(item)
            queue_items.append(item)
        
        db.commit()
        
        for item in queue_items:
            db.refresh(item)
        
        logger.info(f"Added {len(queue_items)} items to queue")
        return queue_items
    
    # PUBLIC_INTERFACE
    def get_queue(self, db: Session) -> List[QueueItem]:
        """
        Get all queued items.
        
        Args:
            db: Database session
            
        Returns:
            List[QueueItem]: Queued items ordered by priority and time
        """
        return db.query(QueueItem).filter(
            QueueItem.status.in_([QueueStatus.QUEUED, QueueStatus.RUNNING])
        ).order_by(
            QueueItem.priority.desc(),
            QueueItem.queued_at.asc()
        ).all()
    
    # PUBLIC_INTERFACE
    def get_next_item(self, db: Session) -> QueueItem:
        """
        Get next item from queue for execution.
        
        Args:
            db: Database session
            
        Returns:
            QueueItem: Next queue item or None
        """
        item = db.query(QueueItem).filter(
            QueueItem.status == QueueStatus.QUEUED
        ).order_by(
            QueueItem.priority.desc(),
            QueueItem.queued_at.asc()
        ).first()
        
        if item:
            item.status = QueueStatus.RUNNING
            item.started_at = datetime.utcnow()
            db.commit()
            db.refresh(item)
        
        return item
    
    # PUBLIC_INTERFACE
    def remove_from_queue(self, db: Session, case_id: str) -> bool:
        """
        Remove a test case from queue.
        
        Args:
            db: Database session
            case_id: Test case ID
            
        Returns:
            bool: True if removed, False if not found
        """
        item = db.query(QueueItem).filter(
            QueueItem.case_id == case_id,
            QueueItem.status == QueueStatus.QUEUED
        ).first()
        
        if not item:
            return False
        
        item.status = QueueStatus.CANCELLED
        item.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Removed case {case_id} from queue")
        return True
    
    # PUBLIC_INTERFACE
    def complete_queue_item(self, db: Session, item_id: str, run_id: str, success: bool):
        """
        Mark a queue item as completed.
        
        Args:
            db: Database session
            item_id: Queue item ID
            run_id: Associated run ID
            success: Whether execution was successful
        """
        item = db.query(QueueItem).filter(QueueItem.id == item_id).first()
        
        if item:
            item.status = QueueStatus.COMPLETED if success else QueueStatus.FAILED
            item.run_id = run_id
            item.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Completed queue item {item_id} with run {run_id}")


# Global queue service instance
queue_service = QueueService()
