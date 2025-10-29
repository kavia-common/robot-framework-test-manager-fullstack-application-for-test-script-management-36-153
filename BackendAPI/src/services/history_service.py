"""
Service for managing run history and logs.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.models import RunHistory, ExecutionStatus
from src.services.storage_service import storage_service
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HistoryService:
    """Service for run history management."""
    
    # PUBLIC_INTERFACE
    def get_run_history(self, db: Session, run_id: str) -> Optional[RunHistory]:
        """
        Get run history by ID.
        
        Args:
            db: Database session
            run_id: Run ID
            
        Returns:
            RunHistory: Run history or None
        """
        return db.query(RunHistory).filter(RunHistory.run_id == run_id).first()
    
    # PUBLIC_INTERFACE
    def list_run_histories(self, db: Session, case_id: Optional[str] = None, 
                          status: Optional[str] = None, skip: int = 0, 
                          limit: int = 100) -> List[RunHistory]:
        """
        List run histories with filtering.
        
        Args:
            db: Database session
            case_id: Filter by case ID
            status: Filter by status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[RunHistory]: List of run histories
        """
        query = db.query(RunHistory)
        
        if case_id:
            query = query.filter(RunHistory.case_id == case_id)
        if status:
            query = query.filter(RunHistory.status == ExecutionStatus(status))
        
        return query.order_by(RunHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    # PUBLIC_INTERFACE
    def get_log_url(self, db: Session, run_id: str) -> Optional[str]:
        """
        Get presigned URL for run log.
        
        Args:
            db: Database session
            run_id: Run ID
            
        Returns:
            str: Presigned log URL or None
        """
        run = self.get_run_history(db, run_id)
        
        if not run or not run.log_object_key:
            return None
        
        try:
            return storage_service.get_log_url(run.log_object_key)
        except Exception as e:
            logger.error(f"Failed to generate log URL for run {run_id}: {str(e)}")
            return None
    
    # PUBLIC_INTERFACE
    def delete_run_history(self, db: Session, run_id: str):
        """
        Delete run history and associated logs.
        
        Args:
            db: Database session
            run_id: Run ID
        """
        run = self.get_run_history(db, run_id)
        
        if not run:
            raise ValueError("Run history not found")
        
        # Delete log from storage if exists
        if run.log_object_key:
            try:
                from src.config import settings
                storage_service.delete_object(settings.minio_bucket_logs, run.log_object_key)
            except Exception as e:
                logger.error(f"Failed to delete log for run {run_id}: {str(e)}")
        
        # Delete from database
        db.delete(run)
        db.commit()
        
        logger.info(f"Deleted run history {run_id}")
    
    # PUBLIC_INTERFACE
    def get_total_count(self, db: Session, case_id: Optional[str] = None, 
                       status: Optional[str] = None) -> int:
        """
        Get total count of run histories.
        
        Args:
            db: Database session
            case_id: Optional filter by case ID
            status: Optional filter by status
            
        Returns:
            int: Total count
        """
        query = db.query(RunHistory)
        
        if case_id:
            query = query.filter(RunHistory.case_id == case_id)
        if status:
            query = query.filter(RunHistory.status == ExecutionStatus(status))
        
        return query.count()


# Global history service instance
history_service = HistoryService()
