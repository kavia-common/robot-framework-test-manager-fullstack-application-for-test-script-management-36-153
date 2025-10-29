"""
Database models for the Robot Framework Test Manager.
Contains all SQLAlchemy ORM models for PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, 
    ForeignKey, Boolean, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
import enum
import uuid

from src.database.session import Base


def generate_uuid():
    """Generate UUID as string."""
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    TESTER = "tester"
    VIEWER = "viewer"


class ExecutionStatus(str, enum.Enum):
    """Test execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class QueueStatus(str, enum.Enum):
    """Queue item status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.TESTER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    test_scripts = relationship("TestScript", back_populates="created_by_user", foreign_keys="TestScript.created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class TestScript(Base):
    """Test script model."""
    
    __tablename__ = "test_scripts"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    metadata = Column(JSON, default=dict)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    created_by_user = relationship("User", back_populates="test_scripts", foreign_keys=[created_by])
    test_cases = relationship("TestCase", back_populates="test_script", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_test_scripts_created_by", "created_by"),
        Index("idx_test_scripts_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<TestScript(id={self.id}, name={self.name})>"


class TestCase(Base):
    """Test case model."""
    
    __tablename__ = "test_cases"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    test_script_id = Column(String, ForeignKey("test_scripts.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    variables = Column(JSON, default=dict)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    test_script = relationship("TestScript", back_populates="test_cases")
    run_histories = relationship("RunHistory", back_populates="test_case", cascade="all, delete-orphan")
    queue_items = relationship("QueueItem", back_populates="test_case", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_test_cases_script_id", "test_script_id"),
        Index("idx_test_cases_created_by", "created_by"),
        Index("idx_test_cases_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, name={self.name})>"


class RunHistory(Base):
    """Run history model for test execution records."""
    
    __tablename__ = "run_histories"
    
    run_id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=False)
    status = Column(SQLEnum(ExecutionStatus), nullable=False, default=ExecutionStatus.PENDING)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    log_url = Column(String(500))
    log_object_key = Column(String(500))
    error_message = Column(Text)
    execution_details = Column(JSON, default=dict)
    triggered_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="run_histories")
    
    # Indexes
    __table_args__ = (
        Index("idx_run_histories_case_id", "case_id"),
        Index("idx_run_histories_status", "status"),
        Index("idx_run_histories_started_at", "started_at"),
        Index("idx_run_histories_triggered_by", "triggered_by"),
    )
    
    def __repr__(self):
        return f"<RunHistory(run_id={self.run_id}, case_id={self.case_id}, status={self.status})>"


class QueueItem(Base):
    """Queue item model for test case execution queue."""
    
    __tablename__ = "queue_items"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    case_id = Column(String, ForeignKey("test_cases.id"), nullable=False)
    status = Column(SQLEnum(QueueStatus), nullable=False, default=QueueStatus.QUEUED)
    priority = Column(Integer, default=0, nullable=False)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    queued_by = Column(String, ForeignKey("users.id"))
    run_id = Column(String, ForeignKey("run_histories.run_id"))
    
    # Relationships
    test_case = relationship("TestCase", back_populates="queue_items")
    
    # Indexes
    __table_args__ = (
        Index("idx_queue_items_case_id", "case_id"),
        Index("idx_queue_items_status", "status"),
        Index("idx_queue_items_priority", "priority"),
        Index("idx_queue_items_queued_at", "queued_at"),
    )
    
    def __repr__(self):
        return f"<QueueItem(id={self.id}, case_id={self.case_id}, status={self.status})>"


class AuditLog(Base):
    """Audit log model for tracking user actions and security events."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
