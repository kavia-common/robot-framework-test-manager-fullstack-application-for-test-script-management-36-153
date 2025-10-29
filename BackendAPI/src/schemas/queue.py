"""
Pydantic schemas for queue management.
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class QueueItemBase(BaseModel):
    """Base queue item schema."""
    case_id: str = Field(..., description="Test case ID")
    status: str = Field(..., description="Queue status")


class QueueItemResponse(QueueItemBase):
    """Schema for queue item response."""
    id: str = Field(..., description="Queue item ID")
    queued_at: datetime = Field(..., description="Timestamp when queued")
    priority: int = Field(..., description="Queue priority")
    
    class Config:
        from_attributes = True


class QueueAddRequest(BaseModel):
    """Schema for adding items to queue."""
    case_ids: List[str] = Field(..., min_length=1, description="List of test case IDs to queue")


class ExecuteRequest(BaseModel):
    """Schema for test execution request."""
    case_ids: List[str] = Field(..., min_length=1, description="List of test case IDs to execute")
    run_type: str = Field(..., description="Run type: ad_hoc or queued")
    
    class Config:
        use_enum_values = True
