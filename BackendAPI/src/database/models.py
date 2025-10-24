from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

Base = declarative_base()

class ExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QueueStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Auth-related models removed - all endpoints are now public

class TestScript(Base):
    __tablename__ = "test_scripts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    content = Column(Text)  # Robot Framework script content
    script_metadata = Column(JSON)  # Renamed to avoid conflict with SQLAlchemy metadata
    file_path = Column(String(500))  # MinIO file path
    created_by = Column(String, nullable=True)  # Nullable - no user authentication
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    test_cases = relationship("TestCase", back_populates="test_script", cascade="all, delete-orphan")

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(String, ForeignKey("test_scripts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    variables = Column(JSON)  # Test case variables and configuration
    created_by = Column(String, nullable=True)  # Nullable - no user authentication
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    test_script = relationship("TestScript", back_populates="test_cases")
    queue_items = relationship("QueueItem", back_populates="test_case")
    run_histories = relationship("RunHistory", back_populates="test_case")

class QueueItem(Base):
    __tablename__ = "queue_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(QueueStatus), default=QueueStatus.QUEUED, nullable=False)
    priority = Column(Integer, default=1)  # Higher number = higher priority
    config = Column(JSON)  # Execution configuration
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    test_case = relationship("TestCase", back_populates="queue_items")

class RunHistory(Base):
    __tablename__ = "run_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ExecutionStatus), nullable=False)
    executed_by = Column(String, nullable=True)  # Nullable - no user authentication
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    log_file_path = Column(String(500))  # MinIO path to log files
    results = Column(JSON)  # Execution results and metrics
    error_message = Column(Text)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="run_histories")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # Nullable - no user authentication
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, EXECUTE, etc.
    resource_type = Column(String(50), nullable=False)  # TestScript, TestCase, etc.
    resource_id = Column(String(100))
    details = Column(JSON)  # Additional context
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
