"""
SQLAlchemy database models for the Robot Framework Test Manager.
Defines all database tables and relationships.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from src.database.connection import Base


class RoleEnum(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TESTER = "tester"
    VIEWER = "viewer"


class StatusEnum(str, enum.Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"


class RunTypeEnum(str, enum.Enum):
    """Run type enumeration"""
    AD_HOC = "ad_hoc"
    QUEUED = "queued"
    SCHEDULED = "scheduled"


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    created_tests = relationship("TestScript", back_populates="creator", foreign_keys="TestScript.created_by")


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Enum(RoleEnum), unique=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    users = relationship("UserRole", back_populates="role")


class UserRole(Base):
    """Many-to-many relationship between users and roles"""
    __tablename__ = "user_roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class TestScript(Base):
    """Test script model"""
    __tablename__ = "test_scripts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    meta_data = Column(JSON, default={})
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_tests", foreign_keys=[created_by])
    test_cases = relationship("TestCase", back_populates="test_script", cascade="all, delete-orphan")


class TestCase(Base):
    """Test case model"""
    __tablename__ = "test_cases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_script_id = Column(String(36), ForeignKey("test_scripts.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    variables = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    test_script = relationship("TestScript", back_populates="test_cases")
    queue_items = relationship("QueueItem", back_populates="test_case", cascade="all, delete-orphan")
    run_histories = relationship("RunHistory", back_populates="test_case", cascade="all, delete-orphan")


class QueueItem(Base):
    """Queue item model for test execution queue"""
    __tablename__ = "queue_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    priority = Column(Integer, default=0)
    queued_at = Column(DateTime, default=datetime.utcnow)
    queued_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    test_case = relationship("TestCase", back_populates="queue_items")


class RunHistory(Base):
    """Run history model for test execution records"""
    __tablename__ = "run_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("test_cases.id"), nullable=False)
    run_type = Column(Enum(RunTypeEnum), nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    triggered_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_case = relationship("TestCase", back_populates="run_histories")
    logs = relationship("Log", back_populates="run_history", cascade="all, delete-orphan")


class Log(Base):
    """Log model for execution logs"""
    __tablename__ = "logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("run_history.id"), nullable=False)
    log_content = Column(Text)
    log_file_path = Column(String(500))  # Path in MinIO
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run_history = relationship("RunHistory", back_populates="logs")
