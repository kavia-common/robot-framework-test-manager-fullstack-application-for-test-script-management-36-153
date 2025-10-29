"""
Pydantic schemas for test scripts.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TestScriptBase(BaseModel):
    """Base test script schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Test script name")
    description: Optional[str] = Field(None, description="Test script description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TestScriptCreate(TestScriptBase):
    """Schema for test script creation."""
    pass


class TestScriptUpdate(BaseModel):
    """Schema for test script update."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Test script name")
    description: Optional[str] = Field(None, description="Test script description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TestScriptResponse(TestScriptBase):
    """Schema for test script response."""
    id: str = Field(..., description="Test script ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
