"""
Pydantic schemas for test scripts, test cases, queue, history, and logs.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# Test Script Schemas
class TestScriptBase(BaseModel):
    """Base test script schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}


class TestScriptCreate(TestScriptBase):
    """Schema for creating a test script"""
    pass


class TestScriptUpdate(BaseModel):
    """Schema for updating a test script"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class TestScriptResponse(TestScriptBase):
    """Schema for test script response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Test Case Schemas
class TestCaseBase(BaseModel):
    """Base test case schema"""
    test_script_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = {}


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case"""
    pass


class TestCaseUpdate(BaseModel):
    """Schema for updating a test case"""
    test_script_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class TestCaseResponse(TestCaseBase):
    """Schema for test case response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Queue Schemas
class QueueItemBase(BaseModel):
    """Base queue item schema"""
    case_id: str
    priority: Optional[int] = 0


class QueueItemCreate(QueueItemBase):
    """Schema for creating a queue item"""
    pass


class QueueItemResponse(BaseModel):
    """Schema for queue item response"""
    case_id: str
    status: str
    queued_at: datetime
    priority: Optional[int] = 0
    
    class Config:
        from_attributes = True


class QueueAddRequest(BaseModel):
    """Schema for adding items to queue"""
    case_ids: List[str]


# Execution Schemas
class ExecuteRequest(BaseModel):
    """Schema for execution request"""
    case_ids: List[str]
    run_type: str = Field(..., pattern="^(ad_hoc|queued)$")


# Run History Schemas
class RunHistoryResponse(BaseModel):
    """Schema for run history response"""
    run_id: str
    case_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    log_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# Log Schemas
class LogResponse(BaseModel):
    """Schema for log response"""
    log_url: str


# Pagination Schema
class PaginationResponse(BaseModel):
    """Schema for paginated responses"""
    items: List[Any]
    total: int
    page: int
    page_size: int


# Standard Response Schemas
class StandardResponse(BaseModel):
    """Standard API response schema"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str
