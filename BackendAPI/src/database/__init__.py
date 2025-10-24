"""
Database package for Robot Framework Test Manager.

Contains SQLAlchemy models, database connection management,
and initialization utilities.
"""

from .models import (
    Base,
    TestScript,
    TestCase,
    QueueItem,
    RunHistory,
    AuditLog,
    ExecutionStatus,
    QueueStatus
)
from .connection import get_db, create_tables, init_db

__all__ = [
    'Base',
    'TestScript',
    'TestCase',
    'QueueItem',
    'RunHistory',
    'AuditLog',
    'ExecutionStatus',
    'QueueStatus',
    'get_db',
    'create_tables', 
    'init_db'
]
