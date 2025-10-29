"""
Pydantic schemas for run history.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class RunHistoryBase(BaseModel):
    """Base run history schema."""
    run_id: str = Field(..., description="Run ID")
    case_id: str = Field(..., description="Test case ID")
    status: str = Field(..., description="Execution status")


class RunHistoryResponse(RunHistoryBase):
    """Schema for run history response."""
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Finish timestamp")
    log_url: Optional[str] = Field(None, description="Log file URL")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution details")
    
    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    """Schema for log response."""
    log_url: str = Field(..., description="Pre-signed URL to download log")
