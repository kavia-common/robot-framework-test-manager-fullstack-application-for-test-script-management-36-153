"""
Service for managing test scripts.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.models import TestScript
from src.schemas.test_script import TestScriptCreate, TestScriptUpdate
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TestService:
    """Service for test script management."""
    
    # PUBLIC_INTERFACE
    def create_test_script(self, db: Session, script_data: TestScriptCreate, user_id: str) -> TestScript:
        """
        Create a new test script.
        
        Args:
            db: Database session
            script_data: Test script creation data
            user_id: ID of user creating the script
            
        Returns:
            TestScript: Created test script
        """
        script = TestScript(
            name=script_data.name,
            description=script_data.description,
            metadata=script_data.metadata,
            created_by=user_id
        )
        
        db.add(script)
        db.commit()
        db.refresh(script)
        
        logger.info(f"Created test script: {script.name} (ID: {script.id})")
        return script
    
    # PUBLIC_INTERFACE
    def get_test_script(self, db: Session, script_id: str) -> Optional[TestScript]:
        """
        Get a test script by ID.
        
        Args:
            db: Database session
            script_id: Test script ID
            
        Returns:
            TestScript: Test script or None
        """
        return db.query(TestScript).filter(
            TestScript.id == script_id,
            TestScript.is_deleted == False
        ).first()
    
    # PUBLIC_INTERFACE
    def list_test_scripts(self, db: Session, skip: int = 0, limit: int = 100) -> List[TestScript]:
        """
        List all test scripts.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[TestScript]: List of test scripts
        """
        return db.query(TestScript).filter(
            TestScript.is_deleted == False
        ).order_by(TestScript.created_at.desc()).offset(skip).limit(limit).all()
    
    # PUBLIC_INTERFACE
    def update_test_script(self, db: Session, script_id: str, script_data: TestScriptUpdate) -> TestScript:
        """
        Update a test script.
        
        Args:
            db: Database session
            script_id: Test script ID
            script_data: Update data
            
        Returns:
            TestScript: Updated test script
        """
        script = self.get_test_script(db, script_id)
        if not script:
            raise ValueError("Test script not found")
        
        if script_data.name is not None:
            script.name = script_data.name
        if script_data.description is not None:
            script.description = script_data.description
        if script_data.metadata is not None:
            script.metadata = script_data.metadata
        
        db.commit()
        db.refresh(script)
        
        logger.info(f"Updated test script: {script.name} (ID: {script.id})")
        return script
    
    # PUBLIC_INTERFACE
    def delete_test_script(self, db: Session, script_id: str):
        """
        Soft delete a test script.
        
        Args:
            db: Database session
            script_id: Test script ID
        """
        script = self.get_test_script(db, script_id)
        if not script:
            raise ValueError("Test script not found")
        
        script.is_deleted = True
        db.commit()
        
        logger.info(f"Deleted test script: {script.name} (ID: {script.id})")
    
    # PUBLIC_INTERFACE
    def get_total_count(self, db: Session) -> int:
        """
        Get total count of test scripts.
        
        Args:
            db: Database session
            
        Returns:
            int: Total count
        """
        return db.query(TestScript).filter(TestScript.is_deleted == False).count()


# Global test service instance
test_service = TestService()
