"""
Structured logging utilities for the application.
"""

import logging
import structlog
from src.config import settings

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)


# PUBLIC_INTERFACE
def get_logger(name: str = __name__):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# PUBLIC_INTERFACE
def audit_log(action: str, user_id: str, resource_type: str = None, 
              resource_id: str = None, details: dict = None):
    """
    Create an audit log entry.
    
    Args:
        action: Action performed
        user_id: User who performed the action
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        details: Additional details
    """
    logger = get_logger("audit")
    logger.info(
        "audit_event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {}
    )
