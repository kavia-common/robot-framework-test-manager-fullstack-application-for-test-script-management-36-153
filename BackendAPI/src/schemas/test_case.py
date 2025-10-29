"""
Pydantic schemas for test cases.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TestCaseBase(BaseModel):
    """Base test case schema."""
    test_script_id: str = Field(..., description="Test script ID")
    name: str = Field(..., min_length=1, max_length=255, description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Test variables")


class TestCaseCreate(TestCaseBase):
    """Schema for test case creation."""
    pass


class TestCaseUpdate(BaseModel):
    """Schema for test case update."""
    test_script_id: Optional[str] = Field(None, description="Test script ID")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    variables: Optional[Dict[str, Any]] = Field(None, description="Test variables")


class TestCaseResponse(TestCaseBase):
    """Schema for test case response."""
    id: str = Field(..., description="Test case ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
