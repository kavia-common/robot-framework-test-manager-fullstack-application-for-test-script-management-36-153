"""
Service for managing test cases.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.models import TestCase
from src.schemas.test_case import TestCaseCreate, TestCaseUpdate
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CaseService:
    """Service for test case management."""
    
    # PUBLIC_INTERFACE
    def create_test_case(self, db: Session, case_data: TestCaseCreate, user_id: str) -> TestCase:
        """
        Create a new test case.
        
        Args:
            db: Database session
            case_data: Test case creation data
            user_id: ID of user creating the case
            
        Returns:
            TestCase: Created test case
        """
        case = TestCase(
            test_script_id=case_data.test_script_id,
            name=case_data.name,
            description=case_data.description,
            variables=case_data.variables,
            created_by=user_id
        )
        
        db.add(case)
        db.commit()
        db.refresh(case)
        
        logger.info(f"Created test case: {case.name} (ID: {case.id})")
        return case
    
    # PUBLIC_INTERFACE
    def get_test_case(self, db: Session, case_id: str) -> Optional[TestCase]:
        """
        Get a test case by ID.
        
        Args:
            db: Database session
            case_id: Test case ID
            
        Returns:
            TestCase: Test case or None
        """
        return db.query(TestCase).filter(
            TestCase.id == case_id,
            TestCase.is_deleted == False
        ).first()
    
    # PUBLIC_INTERFACE
    def list_test_cases(self, db: Session, test_script_id: Optional[str] = None, 
                       name: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[TestCase]:
        """
        List test cases with optional filtering.
        
        Args:
            db: Database session
            test_script_id: Filter by test script ID
            name: Filter by name (partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[TestCase]: List of test cases
        """
        query = db.query(TestCase).filter(TestCase.is_deleted == False)
        
        if test_script_id:
            query = query.filter(TestCase.test_script_id == test_script_id)
        if name:
            query = query.filter(TestCase.name.ilike(f"%{name}%"))
        
        return query.order_by(TestCase.created_at.desc()).offset(skip).limit(limit).all()
    
    # PUBLIC_INTERFACE
    def update_test_case(self, db: Session, case_id: str, case_data: TestCaseUpdate) -> TestCase:
        """
        Update a test case.
        
        Args:
            db: Database session
            case_id: Test case ID
            case_data: Update data
            
        Returns:
            TestCase: Updated test case
        """
        case = self.get_test_case(db, case_id)
        if not case:
            raise ValueError("Test case not found")
        
        if case_data.test_script_id is not None:
            case.test_script_id = case_data.test_script_id
        if case_data.name is not None:
            case.name = case_data.name
        if case_data.description is not None:
            case.description = case_data.description
        if case_data.variables is not None:
            case.variables = case_data.variables
        
        db.commit()
        db.refresh(case)
        
        logger.info(f"Updated test case: {case.name} (ID: {case.id})")
        return case
    
    # PUBLIC_INTERFACE
    def delete_test_case(self, db: Session, case_id: str):
        """
        Soft delete a test case.
        
        Args:
            db: Database session
            case_id: Test case ID
        """
        case = self.get_test_case(db, case_id)
        if not case:
            raise ValueError("Test case not found")
        
        case.is_deleted = True
        db.commit()
        
        logger.info(f"Deleted test case: {case.name} (ID: {case.id})")
    
    # PUBLIC_INTERFACE
    def get_total_count(self, db: Session, test_script_id: Optional[str] = None) -> int:
        """
        Get total count of test cases.
        
        Args:
            db: Database session
            test_script_id: Optional filter by test script ID
            
        Returns:
            int: Total count
        """
        query = db.query(TestCase).filter(TestCase.is_deleted == False)
        if test_script_id:
            query = query.filter(TestCase.test_script_id == test_script_id)
        return query.count()


# Global case service instance
case_service = CaseService()
