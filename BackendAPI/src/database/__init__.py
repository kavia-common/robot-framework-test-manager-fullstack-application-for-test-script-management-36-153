"""
Database package for Robot Framework Test Manager.

Contains SQLAlchemy models, database connection management,
and initialization utilities.
"""

from .models import (
    Base,
    User,
    Role,
    UserRole,
    TestScript,
    TestCase,
    QueueItem,
    RunHistory,
    AuditLog,
    ExecutionStatus,
    QueueStatus,
    UserRoleEnum
)
from .connection import get_db, create_tables, init_db

__all__ = [
    'Base',
    'User',
    'Role', 
    'UserRole',
    'TestScript',
    'TestCase',
    'QueueItem',
    'RunHistory',
    'AuditLog',
    'ExecutionStatus',
    'QueueStatus',
    'UserRoleEnum',
    'get_db',
    'create_tables', 
    'init_db'
]
