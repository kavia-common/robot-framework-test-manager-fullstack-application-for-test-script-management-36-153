"""
Authentication service for user management and JWT token operations.
"""

from sqlalchemy.orm import Session
from typing import Optional

from src.database.models import User, UserRole, AuditLog
from src.schemas.auth import UserCreate, UserUpdate
from src.utils.security import hash_password, verify_password, create_access_token
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication and user management."""
    
    # PUBLIC_INTERFACE
    def create_user(self, db: Session, user_data: UserCreate, role: UserRole = UserRole.TESTER) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            role: User role
            
        Returns:
            User: Created user object
        """
        # Check if username exists
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise ValueError("Username already exists")
        
        # Check if email exists
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise ValueError("Email already exists")
        
        # Create user
        hashed_pw = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_pw,
            role=role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created user: {user.username}")
        return user
    
    # PUBLIC_INTERFACE
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            User: User object if authenticated, None otherwise
        """
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user {username} is inactive")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None
        
        logger.info(f"User authenticated: {username}")
        return user
    
    # PUBLIC_INTERFACE
    def create_token(self, user: User) -> str:
        """
        Create JWT access token for user.
        
        Args:
            user: User object
            
        Returns:
            str: JWT token
        """
        token_data = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value
        }
        
        return create_access_token(token_data)
    
    # PUBLIC_INTERFACE
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User: User object or None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    # PUBLIC_INTERFACE
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User: User object or None
        """
        return db.query(User).filter(User.username == username).first()
    
    # PUBLIC_INTERFACE
    def update_user(self, db: Session, user_id: str, user_data: UserUpdate) -> User:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: Update data
            
        Returns:
            User: Updated user object
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        
        if user_data.email:
            user.email = user_data.email
        if user_data.password:
            user.hashed_password = hash_password(user_data.password)
        if user_data.role:
            user.role = UserRole(user_data.role)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated user: {user.username}")
        return user
    
    # PUBLIC_INTERFACE
    def log_audit_event(self, db: Session, user_id: str, action: str, 
                       resource_type: str = None, resource_id: str = None, 
                       details: dict = None, ip_address: str = None, 
                       user_agent: str = None):
        """
        Log an audit event.
        
        Args:
            db: Database session
            user_id: User ID who performed action
            action: Action description
            resource_type: Type of resource affected
            resource_id: ID of resource
            details: Additional details
            ip_address: Client IP address
            user_agent: Client user agent
        """
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()


# Global auth service instance
auth_service = AuthService()
