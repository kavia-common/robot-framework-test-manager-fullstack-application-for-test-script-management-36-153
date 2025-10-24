"""
Authentication and authorization package.

Contains JWT token handling, password hashing, and role-based
access control (RBAC) functionality.
"""

from .jwt_handler import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    decode_access_token
)
from .rbac import (
    get_current_user,
    require_permission,
    Permission
)

__all__ = [
    'verify_password',
    'get_password_hash', 
    'create_access_token',
    'verify_token',
    'decode_access_token',
    'get_current_user',
    'require_permission',
    'Permission'
]
