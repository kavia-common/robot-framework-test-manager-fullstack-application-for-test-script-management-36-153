from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User, Role, UserRole as UserRoleModel, UserRoleEnum
from .jwt_handler import decode_access_token

security = HTTPBearer()

class Permission:
    """Permission constants for RBAC."""
    
    # Test Script permissions
    CREATE_TEST_SCRIPT = "create_test_script"
    READ_TEST_SCRIPT = "read_test_script"
    UPDATE_TEST_SCRIPT = "update_test_script"
    DELETE_TEST_SCRIPT = "delete_test_script"
    
    # Test Case permissions
    CREATE_TEST_CASE = "create_test_case"
    READ_TEST_CASE = "read_test_case"
    UPDATE_TEST_CASE = "update_test_case"
    DELETE_TEST_CASE = "delete_test_case"
    
    # Execution permissions
    EXECUTE_TEST = "execute_test"
    MANAGE_QUEUE = "manage_queue"
    VIEW_HISTORY = "view_history"
    DELETE_HISTORY = "delete_history"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOGS = "view_audit_logs"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRoleEnum.VIEWER: [
        Permission.READ_TEST_SCRIPT,
        Permission.READ_TEST_CASE,
        Permission.VIEW_HISTORY,
    ],
    UserRoleEnum.TESTER: [
        Permission.READ_TEST_SCRIPT,
        Permission.CREATE_TEST_SCRIPT,
        Permission.UPDATE_TEST_SCRIPT,
        Permission.READ_TEST_CASE,
        Permission.CREATE_TEST_CASE,
        Permission.UPDATE_TEST_CASE,
        Permission.EXECUTE_TEST,
        Permission.MANAGE_QUEUE,
        Permission.VIEW_HISTORY,
    ],
    UserRoleEnum.ADMIN: [
        # Admin has all permissions
        Permission.CREATE_TEST_SCRIPT,
        Permission.READ_TEST_SCRIPT,
        Permission.UPDATE_TEST_SCRIPT,
        Permission.DELETE_TEST_SCRIPT,
        Permission.CREATE_TEST_CASE,
        Permission.READ_TEST_CASE,
        Permission.UPDATE_TEST_CASE,
        Permission.DELETE_TEST_CASE,
        Permission.EXECUTE_TEST,
        Permission.MANAGE_QUEUE,
        Permission.VIEW_HISTORY,
        Permission.DELETE_HISTORY,
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_AUDIT_LOGS,
    ]
}

# PUBLIC_INTERFACE
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        username = decode_access_token(credentials.credentials)
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

# PUBLIC_INTERFACE
def get_user_roles(user: User, db: Session) -> List[UserRoleEnum]:
    """
    Get all roles for a user.
    
    Args:
        user: The user object
        db: Database session
        
    Returns:
        List of user roles
    """
    user_roles = db.query(UserRoleModel).filter(UserRoleModel.user_id == user.id).all()
    roles = []
    for user_role in user_roles:
        role = db.query(Role).filter(Role.id == user_role.role_id).first()
        if role:
            roles.append(role.name)
    return roles

# PUBLIC_INTERFACE
def user_has_permission(user: User, permission: str, db: Session) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user to check
        permission: The permission to check for
        db: Database session
        
    Returns:
        True if user has permission, False otherwise
    """
    user_roles = get_user_roles(user, db)
    
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            if permission in ROLE_PERMISSIONS[role]:
                return True
    
    return False

# PUBLIC_INTERFACE
def require_permission(permission: str):
    """
    Decorator factory to require a specific permission.
    
    Args:
        permission: The required permission
        
    Returns:
        A dependency function that checks the permission
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not user_has_permission(current_user, permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return permission_checker

# Convenience dependencies for common permission checks
require_admin = require_permission(Permission.MANAGE_USERS)
require_tester = require_permission(Permission.EXECUTE_TEST)
require_viewer = require_permission(Permission.READ_TEST_SCRIPT)
