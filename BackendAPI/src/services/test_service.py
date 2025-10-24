"""
Test service for managing test scripts and test cases.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from src.database.models import TestScript, TestCase
from src.schemas.test_schemas import (
    TestScriptCreate, TestScriptUpdate, TestScriptResponse,
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
    PaginationResponse
)


class TestService:
    """Service for test script and test case management"""
    
    # PUBLIC_INTERFACE
    def create_test_script(self, db: Session, test_data: TestScriptCreate, user_id: str) -> TestScriptResponse:
        """
        Create a new test script.
        
        Args:
            db: Database session
            test_data: Test script creation data
            user_id: ID of user creating the test
            
        Returns:
            Created test script
        """
        db_test = TestScript(
            name=test_data.name,
            description=test_data.description,
            meta_data=test_data.meta_data or {},
            created_by=user_id
        )
        db.add(db_test)
        db.commit()
        db.refresh(db_test)
        return TestScriptResponse.model_validate(db_test)
    
    # PUBLIC_INTERFACE
    def get_test_script(self, db: Session, test_id: str) -> Optional[TestScriptResponse]:
        """
        Get a test script by ID.
        
        Args:
            db: Database session
            test_id: Test script ID
            
        Returns:
            Test script if found, None otherwise
        """
        test = db.query(TestScript).filter(TestScript.id == test_id).first()
        if test:
            return TestScriptResponse.model_validate(test)
        return None
    
    # PUBLIC_INTERFACE
    def list_test_scripts(self, db: Session, page: int = 1, page_size: int = 20) -> PaginationResponse:
        """
        List all test scripts with pagination.
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Paginated list of test scripts
        """
        offset = (page - 1) * page_size
        total = db.query(func.count(TestScript.id)).scalar()
        tests = db.query(TestScript).offset(offset).limit(page_size).all()
        
        items = [TestScriptResponse.model_validate(t) for t in tests]
        return PaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # PUBLIC_INTERFACE
    def update_test_script(self, db: Session, test_id: str, test_data: TestScriptUpdate) -> Optional[TestScriptResponse]:
        """
        Update a test script.
        
        Args:
            db: Database session
            test_id: Test script ID
            test_data: Update data
            
        Returns:
            Updated test script if found, None otherwise
        """
        test = db.query(TestScript).filter(TestScript.id == test_id).first()
        if not test:
            return None
        
        update_data = test_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(test, key, value)
        
        db.commit()
        db.refresh(test)
        return TestScriptResponse.model_validate(test)
    
    # PUBLIC_INTERFACE
    def delete_test_script(self, db: Session, test_id: str) -> bool:
        """
        Delete a test script.
        
        Args:
            db: Database session
            test_id: Test script ID
            
        Returns:
            True if deleted, False if not found
        """
        test = db.query(TestScript).filter(TestScript.id == test_id).first()
        if not test:
            return False
        
        db.delete(test)
        db.commit()
        return True
    
    # PUBLIC_INTERFACE
    def create_test_case(self, db: Session, case_data: TestCaseCreate) -> TestCaseResponse:
        """
        Create a new test case.
        
        Args:
            db: Database session
            case_data: Test case creation data
            
        Returns:
            Created test case
        """
        db_case = TestCase(
            test_script_id=case_data.test_script_id,
            name=case_data.name,
            description=case_data.description,
            variables=case_data.variables or {}
        )
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return TestCaseResponse.model_validate(db_case)
    
    # PUBLIC_INTERFACE
    def get_test_case(self, db: Session, case_id: str) -> Optional[TestCaseResponse]:
        """
        Get a test case by ID.
        
        Args:
            db: Database session
            case_id: Test case ID
            
        Returns:
            Test case if found, None otherwise
        """
        case = db.query(TestCase).filter(TestCase.id == case_id).first()
        if case:
            return TestCaseResponse.model_validate(case)
        return None
    
    # PUBLIC_INTERFACE
    def list_test_cases(
        self, 
        db: Session, 
        test_script_id: Optional[str] = None,
        name: Optional[str] = None,
        page: int = 1, 
        page_size: int = 20
    ) -> PaginationResponse:
        """
        List test cases with optional filtering and pagination.
        
        Args:
            db: Database session
            test_script_id: Optional filter by test script ID
            name: Optional filter by case name (partial match)
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Paginated list of test cases
        """
        query = db.query(TestCase)
        
        if test_script_id:
            query = query.filter(TestCase.test_script_id == test_script_id)
        if name:
            query = query.filter(TestCase.name.ilike(f"%{name}%"))
        
        total = query.count()
        offset = (page - 1) * page_size
        cases = query.offset(offset).limit(page_size).all()
        
        items = [TestCaseResponse.model_validate(c) for c in cases]
        return PaginationResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    # PUBLIC_INTERFACE
    def update_test_case(self, db: Session, case_id: str, case_data: TestCaseUpdate) -> Optional[TestCaseResponse]:
        """
        Update a test case.
        
        Args:
            db: Database session
            case_id: Test case ID
            case_data: Update data
            
        Returns:
            Updated test case if found, None otherwise
        """
        case = db.query(TestCase).filter(TestCase.id == case_id).first()
        if not case:
            return None
        
        update_data = case_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(case, key, value)
        
        db.commit()
        db.refresh(case)
        return TestCaseResponse.model_validate(case)
    
    # PUBLIC_INTERFACE
    def delete_test_case(self, db: Session, case_id: str) -> bool:
        """
        Delete a test case.
        
        Args:
            db: Database session
            case_id: Test case ID
            
        Returns:
            True if deleted, False if not found
        """
        case = db.query(TestCase).filter(TestCase.id == case_id).first()
        if not case:
            return False
        
        db.delete(case)
        db.commit()
        return True


# Global test service instance
test_service = TestService()
