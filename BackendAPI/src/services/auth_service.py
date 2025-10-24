"""
Authentication service for user management and authentication.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta

from src.database.models import User, Role, UserRole, RoleEnum
from src.schemas.user_schemas import UserCreate, LoginRequest, TokenResponse, UserResponse
from src.core.security import verify_password, get_password_hash, create_access_token
from src.core.config import settings


class AuthService:
    """Service for authentication and user management"""
    
    # PUBLIC_INTERFACE
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    # PUBLIC_INTERFACE
    def create_user(self, db: Session, user_data: UserCreate, roles: List[str] = None) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            roles: List of role names to assign to user
            
        Returns:
            Created user object
        """
        if roles is None:
            roles = ["viewer"]
        
        # Create user
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            is_active=1
        )
        db.add(db_user)
        db.flush()
        
        # Assign roles
        for role_name in roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                user_role = UserRole(user_id=db_user.id, role_id=role.id)
                db.add(user_role)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    # PUBLIC_INTERFACE
    def login(self, db: Session, login_data: LoginRequest) -> TokenResponse:
        """
        Login and generate JWT token.
        
        Args:
            db: Database session
            login_data: Login credentials
            
        Returns:
            Token response with JWT
            
        Raises:
            ValueError: If authentication fails
        """
        user = self.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise ValueError("Invalid username or password")
        
        # Get user roles
        roles = [ur.role.name.value for ur in user.roles]
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username, "roles": roles},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(access_token=access_token, token_type="bearer")
    
    # PUBLIC_INTERFACE
    def get_user_info(self, db: Session, user_id: str) -> UserResponse:
        """
        Get user information by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User response with roles
            
        Raises:
            ValueError: If user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        roles = [ur.role.name.value for ur in user.roles]
        
        return UserResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=roles
        )
    
    # PUBLIC_INTERFACE
    def init_default_roles(self, db: Session):
        """
        Initialize default roles if they don't exist.
        
        Args:
            db: Database session
        """
        default_roles = [
            (RoleEnum.ADMIN, "Administrator with full access"),
            (RoleEnum.TESTER, "Tester who can create and execute tests"),
            (RoleEnum.VIEWER, "Viewer with read-only access")
        ]
        
        for role_name, description in default_roles:
            existing_role = db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                role = Role(name=role_name, description=description)
                db.add(role)
        
        db.commit()


# Global auth service instance
auth_service = AuthService()
